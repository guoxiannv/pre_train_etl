#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ArkTS Bad-Case Analysis Pipeline (LLM-based)
--------------------------------------------

Features
- Stratified random sampling (by length bucket, source, language).
- LLM judging with robust JSON extraction & validation.
- Optional consensus (multiple replicas with different temperatures).
- Round summary + per-item JSONL outputs.
- OpenAI-compatible chat API (works with OpenAI or local vLLM endpoints).

Usage
-----
# 1) Prepare your corpus JSONL (each row a dict). Default code field is "text".
# 2) Set environment variables (or pass CLI flags):
#    - OPENAI_API_KEY=...           (for OpenAI or OpenAI-compatible endpoint)
#    - OPENAI_BASE_URL=...          (optional, default: https://api.openai.com/v1)
#
# 3) Run a round of 100-sample judging:
#    python arkts_badcase_pipeline.py \
#        --input example.jsonl --out-dir out_rounds \
#        --n 100 --replicas 2 --model gpt-4o-mini \
#        --concurrency 8 --code-field text
#
# Outputs
# - out_rounds/round_YYYYmmdd_HHMMSS/judgements.jsonl
# - out_rounds/round_YYYYmmdd_HHMMSS/summary.csv
# - out_rounds/round_YYYYmmdd_HHMMSS/sampled.jsonl   (the sampled raw rows)
#
# Notes
# - This script purposely avoids heavy dependencies (no pandas, no jsonschema).
# - You can plug your rule-based logs in post or pre steps outside this script.
"""

import os
import json
import csv
import re
import math
import time
import random
import hashlib
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# Prompt template (system+user merged)
# ----------------------------

PROMPT_TEMPLATE = r"""
你是一个资深 ArkTS/ArkUI 代码语料质检员。目标：在不依赖“硬规则指标”（如许可证、二进制/超长行、自动生成关键词等）的前提下，从「经验/直觉/语义/框架习惯」角度判定一段代码是否适合用于**ArkTS 代码预训练**。

【判定原则】
1) 仅考虑语义质量、ArkTS/ArkUI 习惯性、信息密度与可学习性；不要用诸如“是否二进制/超长行/自动生成/PII/重复”这类硬规则（这些已由前置管线完成）。
2) 允许 TypeScript 代码，只要与 ArkTS 习惯不冲突；但若呈现明显“非 ArkTS 风格”且缺乏学习价值，应判为坏例。
3) 关注以下“经验型坏例信号”（非穷尽）：
   - NON_IDIOMATIC_ARKTS：明显 TS/JS 直译，不符合 ArkTS/ArkUI 习惯（如框架生命周期误用、装饰器错位、HarmonyOS/ArkUI API 范式不对）。
   - TOY_OR_TUTORIAL_FRAGMENT：教学/演示型极短片段，只有 console.log/常量/占位，缺乏可学习结构。
   - TRUNCATED_OR_BROKEN：代码被截断（未闭合括号、悬空注释），上下文依赖严重导致不可编译且缺乏学习价值。
   - SEMANTIC_NON_SENSE：逻辑自相矛盾或无意义（死循环打印、无条件返回占位字符串、滥用异常吞噬）。
   - AI_TONE_OR_TRANSLATIONESE：AI 口癖或翻译腔注释（如“本示例展示如何…”，“As an AI language model…”），模板化措辞。
   - NAMING_STYLE_OUTLIER：极端异常命名/乱码/批量占位（____/a1,a2…/foo_copy_final_final2）。
   - FRAMEWORK_MISUSE：明显误用 ArkUI/HarmonyOS 能力（Ability 生命周期错用、@Component 语义错误、路由/资源访问反常）。
   - HEAVY_NOISE_COMMENTS：与代码无关的长段营销/免责声明/推广，占据主体。
   - LOW_INFORMATION_DUP_PATTERN：虽未被近重命中，但结构极端相似、仅变量/字面量微调的模板近亲。
   - MIXED_LANGUAGE_CONFUSION：跨语言/框架混搭（TS/JS/ArkTS/React/Vue）导致语义混乱。
4) 以“保守不过滤”为原则：若不确定，给出 KEEP_WITH_TAG 并说明原因。

【输出要求（JSON，仅一行）】
{
  "decision": "KEEP" | "KEEP_WITH_TAG" | "REMOVE",
  "labels": ["..."],            // 从上面标签中选；可多选；也可为空
  "arkts_score": 0-5,           // ArkTS 习惯/框架契合度主观分
  "quality_score": 0-5,         // 信息密度/可学习性主观分
  "confidence": 0.0-1.0,        // 你的确信度
  "rationale": "用不超过50字中文/英文，给专业、可复核的理由"
}

【待评审代码】（严格保持原样）：
---CODE-BEGIN---
{code}
---CODE-END---
"""

# ----------------------------
# Data structures
# ----------------------------

@dataclass
class Judgement:
    decision: str
    labels: List[str]
    arkts_score: float
    quality_score: float
    confidence: float
    rationale: str

@dataclass
class ItemResult:
    item_id: str
    replica: int
    decision: str
    labels: List[str]
    arkts_score: float
    quality_score: float
    confidence: float
    rationale: str
    model: str
    temperature: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    raw_response: Optional[str] = None

# ----------------------------
# IO helpers
# ----------------------------

def read_jsonl(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # Skip broken lines
                continue
            if limit is not None and len(rows) >= limit:
                break
    return rows

def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def write_csv(path: Path, rows: List[Dict[str, Any]]):
    if not rows:
        return
    keys = sorted({k for r in rows for k in r.keys()})
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})

# ----------------------------
# Sampling helpers
# ----------------------------

def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def length_bucket_by_chars(s: str) -> str:
    n = len(s)
    if n < 200: return "len_<200"
    if n < 800: return "len_200_800"
    if n < 2000: return "len_800_2k"
    if n < 6000: return "len_2k_6k"
    return "len_6k_plus"

def default_strata(row: Dict[str, Any], code_field: str, source_field: Optional[str], lang_field: Optional[str]) -> Tuple[str, str, str]:
    code = (row.get(code_field) or "") if isinstance(row, dict) else ""
    L = length_bucket_by_chars(code)
    source = str(row.get(source_field)) if (source_field and row.get(source_field) is not None) else "src_unknown"
    lang = str(row.get(lang_field)) if (lang_field and row.get(lang_field) is not None) else "lang_unknown"
    return (L, source, lang)

def stratified_sample(rows: List[Dict[str, Any]], n: int, seed: int, code_field: str="text",
                      source_field: Optional[str]=None, lang_field: Optional[str]=None) -> List[Dict[str, Any]]:
    random.seed(seed)
    # Build strata
    strata = {}
    for r in rows:
        key = default_strata(r, code_field, source_field, lang_field)
        strata.setdefault(key, []).append(r)

    # Proportional allocation + at least 1 per non-empty stratum, then fill remainder
    # Calculate total sizes
    total = len(rows)
    allocation = {}
    remaining = n
    # First pass: proportional floor
    for key, items in strata.items():
        k = max(1, math.floor(len(items) / total * n))
        allocation[key] = min(k, len(items))
        remaining -= allocation[key]

    # If remaining positive, distribute by largest remainders (or just random strata with spare)
    if remaining > 0:
        # Sort strata by available spare size descending
        spare = sorted(
            [(key, len(items) - allocation[key]) for key, items in strata.items() if len(items) > allocation[key]],
            key=lambda x: x[1],
            reverse=True
        )
        idx = 0
        while remaining > 0 and spare:
            key, avail = spare[idx % len(spare)]
            if avail > 0:
                allocation[key] += 1
                remaining -= 1
                spare[idx % len(spare)] = (key, avail - 1)
            idx += 1

    # Sample
    sampled = []
    for key, items in strata.items():
        k = allocation.get(key, 0)
        if k <= 0:
            continue
        sampled.extend(random.sample(items, k) if len(items) > k else list(items))
    # If still not enough due to rounding, fill randomly
    if len(sampled) < n:
        pool = [r for r in rows if r not in sampled]
        extra = random.sample(pool, min(n - len(sampled), len(pool)))
        sampled.extend(extra)

    # Shuffle final
    random.shuffle(sampled)
    return sampled[:n]

# ----------------------------
# OpenAI-compatible client
# ----------------------------

def _http_post(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 60) -> Tuple[int, str]:
    try:
        import requests  # type: ignore
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        return resp.status_code, resp.text
    except Exception:
        # Fallback to urllib
        import urllib.request
        req = urllib.request.Request(url, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)
        data = json.dumps(payload).encode("utf-8")
        try:
            with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                return resp.getcode(), text
        except Exception as e:
            return 0, str(e)

def call_chat_completion(
    prompt: str,
    model: str,
    temperature: float = 0.1,
    max_tokens: int = 512,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 90,
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Call an OpenAI-compatible chat completions API and return the parsed JSON.
    Compatible with OpenAI & local vLLM endpoints.
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    status, text = _http_post(url, headers, payload, timeout=timeout)
    if status != 200:
        return {"error": f"HTTP {status}", "raw": text}

    try:
        data = json.loads(text)
    except Exception:
        return {"error": "Invalid JSON from API", "raw": text}

    return data

# ----------------------------
# JSON extraction & validation
# ----------------------------

JSON_LINE_RE = re.compile(r"\{.*\}", re.DOTALL)

def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    Try to extract the first JSON object from a messy LLM output.
    - Strips code fences if present.
    - Falls back to brace matching.
    """
    s = text.strip()
    # Strip code fences
    if s.startswith("```"):
        # remove leading and trailing code fences
        parts = s.split("```")
        # join the inner parts
        s = "\n".join(parts[1:-1]).strip() if len(parts) >= 3 else s

    # Quick regex
    m = JSON_LINE_RE.search(s)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    # Brace matching fallback
    start_idx = s.find("{")
    while start_idx != -1:
        depth = 0
        for i in range(start_idx, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    chunk = s[start_idx:i+1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        break
        start_idx = s.find("{", start_idx + 1)
    return None

def validate_judgement(obj: Dict[str, Any]) -> Optional[Judgement]:
    try:
        decision = str(obj["decision"]).strip().upper()
        if decision not in ("KEEP", "KEEP_WITH_TAG", "REMOVE"):
            return None
        labels = obj.get("labels", [])
        if labels is None:
            labels = []
        if not isinstance(labels, list):
            return None
        arkts_score = float(obj.get("arkts_score", 0))
        quality_score = float(obj.get("quality_score", 0))
        confidence = float(obj.get("confidence", 0))
        rationale = str(obj.get("rationale", ""))[:400]

        # Bound checks
        arkts_score = max(0.0, min(5.0, arkts_score))
        quality_score = max(0.0, min(5.0, quality_score))
        confidence = max(0.0, min(1.0, confidence))

        return Judgement(
            decision=decision,
            labels=[str(x) for x in labels],
            arkts_score=arkts_score,
            quality_score=quality_score,
            confidence=confidence,
            rationale=rationale
        )
    except Exception:
        return None

# ----------------------------
# Consensus logic
# ----------------------------

SEVERITY = {"KEEP": 0, "KEEP_WITH_TAG": 1, "REMOVE": 2}

def consensus(judgements: List[Judgement]) -> Judgement:
    if not judgements:
        return Judgement("KEEP_WITH_TAG", [], 3.0, 3.0, 0.3, "empty-judgements")

    # Majority by decision; tie-break by max severity; average scores/confidence
    vote = {}
    for j in judgements:
        vote[j.decision] = vote.get(j.decision, 0) + 1
    # Find majority
    max_votes = max(vote.values())
    top = [d for d, c in vote.items() if c == max_votes]
    if len(top) == 1:
        final_decision = top[0]
    else:
        # Tie: choose the one with greater severity; if still tie, KEEP_WITH_TAG
        final_decision = sorted(top, key=lambda d: SEVERITY[d], reverse=True)[0]
        if len(top) > 1 and SEVERITY[top[0]] == SEVERITY[top[-1]]:
            final_decision = "KEEP_WITH_TAG"

    # Aggregate labels & scores
    labels = sorted({l for j in judgements for l in j.labels})
    arkts_score = sum(j.arkts_score for j in judgements) / len(judgements)
    quality_score = sum(j.quality_score for j in judgements) / len(judgements)
    confidence = sum(j.confidence for j in judgements) / len(judgements)
    rationale = "; ".join((j.rationale or "") for j in judgements)[:400]
    return Judgement(final_decision, labels, arkts_score, quality_score, confidence, rationale)

# ----------------------------
# Main judging routine
# ----------------------------

def build_prompt(code: str) -> str:
    return PROMPT_TEMPLATE.replace("{code}", code)

def run_one_judgement(
    item_id: str,
    code: str,
    model: str,
    temperature: float,
    api_key: Optional[str],
    base_url: Optional[str],
    max_tokens: int,
    timeout: int,
    replica: int
) -> ItemResult:
    prompt = build_prompt(code)
    resp = call_chat_completion(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout
    )

    raw_text = None
    usage = {}
    if "error" in resp:
        # Synthesize a KEEP_WITH_TAG low-confidence result with error info
        j = Judgement("KEEP_WITH_TAG", ["API_ERROR"], 3.0, 3.0, 0.2, str(resp["error"])[:200])
    else:
        try:
            choice = resp["choices"][0]["message"]["content"]
            raw_text = choice
        except Exception:
            raw_text = json.dumps(resp)[:2000]

        obj = extract_json_object(raw_text or "")
        j = validate_judgement(obj) if obj else None
        if not j:
            j = Judgement("KEEP_WITH_TAG", ["PARSE_ERROR"], 3.0, 3.0, 0.3, "Failed to parse model JSON")

        usage = resp.get("usage", {}) if isinstance(resp, dict) else {}

    return ItemResult(
        item_id=item_id,
        replica=replica,
        decision=j.decision,
        labels=j.labels,
        arkts_score=j.arkts_score,
        quality_score=j.quality_score,
        confidence=j.confidence,
        rationale=j.rationale,
        model=model,
        temperature=temperature,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
        raw_response=raw_text
    )

def run_round(
    input_path: Path,
    out_dir: Path,
    n: int = 100,
    replicas: int = 2,
    model: str = "gpt-4o-mini",
    temps: Optional[List[float]] = None,
    code_field: str = "text",
    source_field: Optional[str] = None,
    lang_field: Optional[str] = None,
    concurrency: int = 8,
    seed: int = 42,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: int = 512,
    timeout: int = 90
):
    temps = temps or [0.1, 0.3]
    rows = read_jsonl(input_path)
    if not rows:
        raise SystemExit(f"No rows loaded from {input_path}")

    # Stratified sample
    sampled = stratified_sample(rows, n=n, seed=seed, code_field=code_field,
                                source_field=source_field, lang_field=lang_field)

    # Prepare round directory
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    round_dir = out_dir / f"round_{ts}"
    round_dir.mkdir(parents=True, exist_ok=True)

    # Persist sampled raw rows
    write_jsonl(round_dir / "sampled.jsonl", sampled)

    # Fan out to LLM
    jobs = []
    item_map = {}
    for idx, r in enumerate(sampled):
        code = r.get(code_field) or ""
        item_id = r.get("id") or sha1_text(code)  # ensure stable id
        item_map[item_id] = r
        for rep in range(replicas):
            t = temps[min(rep, len(temps)-1)]
            jobs.append((item_id, code, rep+1, t))

    results: List[ItemResult] = []
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY", None)
    base_url = base_url or os.getenv("DASHSCOPE_BASE_URL", None)

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = []
        for (item_id, code, replica, t) in jobs:
            fut = ex.submit(run_one_judgement, item_id, code, model, t, api_key, base_url, max_tokens, timeout, replica)
            futs.append(fut)
        for fut in as_completed(futs):
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                # Record a synthetic error result
                results.append(ItemResult(
                    item_id="UNKNOWN",
                    replica=0,
                    decision="KEEP_WITH_TAG",
                    labels=["EXEC_ERROR"],
                    arkts_score=3.0, quality_score=3.0, confidence=0.2,
                    rationale=str(e)[:200],
                    model=model,
                    temperature=0.0
                ))

    # Group by item and build consensus
    by_item: Dict[str, List[ItemResult]] = {}
    for r in results:
        by_item.setdefault(r.item_id, []).append(r)

    final_rows = []
    for item_id, lst in by_item.items():
        js = [Judgement(d.decision, d.labels, d.arkts_score, d.quality_score, d.confidence, d.rationale) for d in lst]
        J = consensus(js)
        raw = item_map.get(item_id, {})
        final_rows.append({
            "item_id": item_id,
            "final_decision": J.decision,
            "final_labels": J.labels,
            "final_arkts_score": round(J.arkts_score, 3),
            "final_quality_score": round(J.quality_score, 3),
            "final_confidence": round(J.confidence, 3),
            "rationale_sample": J.rationale,
            "replicas": len(lst),
            "source": raw.get(source_field) if source_field else None,
            "lang": raw.get(lang_field) if lang_field else None,
            "len_chars": len((raw.get(code_field) or "")),
        })

    # Write per-replica judgements with original fields
    replica_rows = []
    for r in results:
        row_dict = asdict(r)
        # Add original fields from input
        original_item = item_map.get(r.item_id, {})
        # Merge original fields, but don't overwrite judgement fields
        merged_row = {**original_item, **row_dict}
        replica_rows.append(merged_row)
    write_jsonl(round_dir / "judgements.jsonl", replica_rows)

    # Write final summary table
    write_csv(round_dir / "summary.csv", final_rows)

    # Also print a quick console summary
    counts = {"KEEP": 0, "KEEP_WITH_TAG": 0, "REMOVE": 0}
    for r in final_rows:
        counts[r["final_decision"]] += 1
    print("=== Round Summary ===")
    print("Total sampled:", len(sampled))
    print("Final decisions:", counts)
    print("Output dir:", round_dir)

# ----------------------------
# CLI
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="ArkTS Bad-Case Analysis Pipeline (LLM-based)")
    ap.add_argument("--input", type=str, required=True, help="Path to corpus JSONL")
    ap.add_argument("--out-dir", type=str, default="out_rounds", help="Output directory")
    ap.add_argument("--n", type=int, default=100, help="Number of samples per round")
    ap.add_argument("--replicas", type=int, default=2, help="Number of LLM replicas per item")
    ap.add_argument("--model", type=str, default="qwen3-coder-480b-a35b-instruct", help="Model name for OpenAI-compatible API")
    ap.add_argument("--temps", type=str, default="0.1,0.3", help="Comma-separated temperatures, e.g., 0.0,0.2")
    ap.add_argument("--code-field", type=str, default="text", help="Field name containing code text")
    ap.add_argument("--source-field", type=str, default=None, help="Optional field for source strata (e.g., repo)")
    ap.add_argument("--lang-field", type=str, default=None, help="Optional field for language strata")
    ap.add_argument("--concurrency", type=int, default=8, help="Parallel requests")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    ap.add_argument("--api-key", type=str, default=None, help="API key (else env OPENAI_API_KEY)")
    ap.add_argument("--base-url", type=str, default=None, help="API base URL (else env OPENAI_BASE_URL)")
    ap.add_argument("--max-tokens", type=int, default=512, help="Max tokens for completion")
    ap.add_argument("--timeout", type=int, default=90, help="HTTP timeout seconds")

    args = ap.parse_args()
    temps = [float(x.strip()) for x in args.temps.split(",") if x.strip()]

    run_round(
        input_path=Path(args.input),
        out_dir=Path(args.out_dir),
        n=args.n,
        replicas=args.replicas,
        model=args.model,
        temps=temps,
        code_field=args.code_field,
        source_field=args.source_field,
        lang_field=args.lang_field,
        concurrency=args.concurrency,
        seed=args.seed,
        api_key=args.api_key,
        base_url=args.base_url,
        max_tokens=args.max_tokens,
        timeout=args.timeout
    )

if __name__ == "__main__":
    main()
