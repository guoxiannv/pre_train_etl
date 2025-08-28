#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ArkTS Full Data Processing Pipeline (LLM-based) - No Sampling
------------------------------------------------------------

Features
- Process ALL data without sampling
- Resume capability (skip already processed items)
- LLM judging with robust JSON extraction & validation
- Optional consensus (multiple replicas with different temperatures)
- Progress tracking and checkpoint saving
- OpenAI-compatible chat API (works with OpenAI or local vLLM endpoints)

Usage
-----
# 1) Prepare your corpus JSONL (each row a dict). Default code field is "text".
# 2) Set environment variables (or pass CLI flags):
#    - OPENAI_API_KEY=...           (for OpenAI or OpenAI-compatible endpoint)
#    - OPENAI_BASE_URL=...          (optional, default: https://api.openai.com/v1)
#
# 3) Run full data processing:
#    python arkts_full_data_processor.py \
#        --input example.jsonl --out-dir out_full \
#        --replicas 2 --model gpt-4o-mini \
#        --concurrency 8 --code-field text
#
# Outputs
# - out_full/judgements.jsonl (all judgements)
# - out_full/summary.csv (final summary)
# - out_full/progress.json (progress tracking)
# - out_full/processed_ids.txt (processed item IDs for resume)
#
# Resume
# - If interrupted, simply run the same command again
# - The script will automatically skip already processed items
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
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义当前脚本路径
SCRIPT_DIR = Path(__file__).parent.absolute()

# ----------------------------
# Prompt template (system+user merged)
# ----------------------------

PROMPT_TEMPLATE = r"""
你是一个资深 ArkTS/ArkUI 代码语料质检员。目标：在不依赖"硬规则指标"（如许可证、二进制/超长行、自动生成关键词等）的前提下，从「经验/直觉/语义/框架习惯」角度判定一段代码是否适合用于**ArkTS 代码预训练**。

【判定原则】
1) 仅考虑语义质量、ArkTS/ArkUI 习惯性、信息密度与可学习性；不要用诸如"是否二进制/超长行/自动生成/PII/重复"这类硬规则（这些已由前置管线完成）。
2) 允许 TypeScript 代码，只要与 ArkTS 习惯不冲突；但若呈现明显"非 ArkTS 风格"且缺乏学习价值，应判为坏例。
3) 关注以下"经验型坏例信号"（非穷尽）：
   - NON_IDIOMATIC_ARKTS：明显 TS/JS 直译，不符合 ArkTS/ArkUI 习惯（如框架生命周期误用、装饰器错位、HarmonyOS/ArkUI API 范式不对）。
   - TOY_OR_TUTORIAL_FRAGMENT：教学/演示型极短片段，只有 console.log/常量/占位，缺乏可学习结构。
   - TRUNCATED_OR_BROKEN：代码被截断（未闭合括号、悬空注释），上下文依赖严重导致不可编译且缺乏学习价值。
   - SEMANTIC_NON_SENSE：逻辑自相矛盾或无意义（死循环打印、无条件返回占位字符串、滥用异常吞噬）。
   - AI_TONE_OR_TRANSLATIONESE：AI 口癖或翻译腔注释（如"本示例展示如何…"，"As an AI language model…"），模板化措辞。
   - NAMING_STYLE_OUTLIER：极端异常命名/乱码/批量占位（____/a1,a2…/foo_copy_final_final2）。
   - FRAMEWORK_MISUSE：明显误用 ArkUI/HarmonyOS 能力（Ability 生命周期错用、@Component 语义错误、路由/资源访问反常）。
   - HEAVY_NOISE_COMMENTS：与代码无关的长段营销/免责声明/推广，占据主体。
   - LOW_INFORMATION_DUP_PATTERN：虽未被近重命中，但结构极端相似、仅变量/字面量微调的模板近亲。
   - MIXED_LANGUAGE_CONFUSION：跨语言/框架混搭（TS/JS/ArkTS/React/Vue）导致语义混乱。
4) 以"保守不过滤"为原则：若不确定，给出 KEEP_WITH_TAG 并说明原因。

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

# Progress tracking removed - using judgements file for resume capability

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

def write_jsonl(path: Path, rows: List[Dict[str, Any]], append: bool = False):
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as f:
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

def load_processed_ids_from_judgements(path: Path) -> Set[str]:
    """Load already processed item IDs from judgements file"""
    if not path.exists():
        return set()
    
    processed_ids = set()
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    item_id = data.get("item_id")
                    if item_id:
                        processed_ids.add(item_id)
                except Exception:
                    continue
    except Exception:
        pass
    
    return processed_ids

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
        ],
        "thinking": {
            "type": "disabled"
        }
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
    # 优先检查脚本目录下是否有JUDGE_PROMPT.txt文件
    prompt_file = SCRIPT_DIR / "JUDGE_PROMPT.txt"
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                custom_prompt = f.read()
            return custom_prompt.replace("{code}", code)
        except Exception as e:
            print(f"Warning: Failed to read JUDGE_PROMPT.txt: {e}, using default template")
    
    return PROMPT_TEMPLATE.replace("{code}", code)

def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

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

def process_full_data(
    input_path: Path,
    out_dir: Path,
    replicas: int = 2,
    model: str = "gpt-4o-mini",
    temps: Optional[List[float]] = None,
    code_field: str = "text",
    concurrency: int = 8,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: int = 512,
    timeout: int = 90,
    batch_size: int = 100
):
    temps = temps or [0.1, 0.3]
    
    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Output files
    judgements_file = out_dir / "judgements.jsonl"
    summary_file = out_dir / "summary.csv"
    
    # Load existing processed IDs from judgements file
    processed_ids = load_processed_ids_from_judgements(judgements_file)
    
    # Load all data
    print("Loading input data...")
    rows = read_jsonl(input_path)
    if not rows:
        raise SystemExit(f"No rows loaded from {input_path}")
    
    # Filter out already processed items
    remaining_rows = []
    for r in rows:
        code = r.get(code_field) or ""
        item_id = r.get("id") or sha1_text(code)
        if item_id not in processed_ids:
            remaining_rows.append(r)
    
    total_items = len(rows)
    remaining_items = len(remaining_rows)
    processed_items = total_items - remaining_items
    
    print(f"Total items: {total_items}")
    print(f"Already processed: {processed_items}")
    print(f"Remaining to process: {remaining_items}")
    
    if remaining_items == 0:
        print("All items have been processed!")
        # Still generate summary in case it doesn't exist
        if judgements_file.exists():
            generate_final_summary(judgements_file, summary_file, replicas)
        return
    
    # Process in batches
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY", None)
    base_url = base_url or os.getenv("DASHSCOPE_BASE_URL", None)
    
    batch_count = 0
    start_time = time.time()
    
    for i in range(0, len(remaining_rows), batch_size):
        batch = remaining_rows[i:i + batch_size]
        batch_count += 1
        
        print(f"\nProcessing batch {batch_count}/{math.ceil(len(remaining_rows) / batch_size)} ({len(batch)} items)...")
        
        # Prepare jobs for this batch
        jobs = []
        item_map = {}
        for r in batch:
            code = r.get(code_field) or ""
            item_id = r.get("id") or sha1_text(code)
            item_map[item_id] = r
            for rep in range(replicas):
                t = temps[min(rep, len(temps)-1)]
                jobs.append((item_id, code, rep+1, t))
        
        # Process batch with threading
        batch_results: List[ItemResult] = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = []
            for (item_id, code, replica, t) in jobs:
                fut = ex.submit(run_one_judgement, item_id, code, model, t, api_key, base_url, max_tokens, timeout, replica)
                futs.append(fut)
            
            for fut in as_completed(futs):
                try:
                    res = fut.result()
                    batch_results.append(res)
                except Exception as e:
                    # Record a synthetic error result
                    batch_results.append(ItemResult(
                        item_id="UNKNOWN",
                        replica=0,
                        decision="KEEP_WITH_TAG",
                        labels=["EXEC_ERROR"],
                        arkts_score=3.0, quality_score=3.0, confidence=0.2,
                        rationale=str(e)[:200],
                        model=model,
                        temperature=0.0
                    ))
        
        # Sort results and save to JSONL
        batch_results.sort(key=lambda x: (x.item_id, x.replica))
        
        # Convert to dict format and append to judgements file
        replica_rows = []
        processed_item_ids = set()
        for r in batch_results:
            row_dict = asdict(r)
            # Add original fields from input
            original_item = item_map.get(r.item_id, {})
            # Merge original fields, but don't overwrite judgement fields
            merged_row = {**original_item, **row_dict}
            replica_rows.append(merged_row)
            processed_item_ids.add(r.item_id)
        
        # Append to judgements file
        write_jsonl(judgements_file, replica_rows, append=True)
        
        # Update progress display
        current_processed = processed_items + (batch_count * batch_size)
        current_processed = min(current_processed, total_items)  # Don't exceed total
        
        # Estimate remaining time
        elapsed_time = time.time() - start_time
        if batch_count > 0:
            items_per_second = (batch_count * batch_size) / elapsed_time
            remaining_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
            estimated_remaining = f"{remaining_seconds / 3600:.1f} hours" if remaining_seconds > 0 else "N/A"
        else:
            estimated_remaining = "N/A"
        
        print(f"Batch {batch_count} completed. Progress: {current_processed}/{total_items} ({current_processed/total_items*100:.1f}%)")
        print(f"Estimated remaining time: {estimated_remaining}")
    
    print("\n=== Processing Complete ===")
    print(f"Total processed: {total_items}/{total_items}")
    
    # Generate final summary
    print("Generating final summary...")
    generate_final_summary(judgements_file, summary_file, replicas)

def generate_final_summary(judgements_file: Path, summary_file: Path, replicas: int):
    """Generate final summary from all judgements"""
    if not judgements_file.exists():
        print("No judgements file found")
        return
    
    # Load all judgements
    all_results = read_jsonl(judgements_file)
    
    # Group by item and build consensus
    by_item: Dict[str, List[ItemResult]] = {}
    for r_dict in all_results:
        # Convert dict back to ItemResult
        r = ItemResult(**{k: v for k, v in r_dict.items() if k in ItemResult.__annotations__})
        by_item.setdefault(r.item_id, []).append(r)
    
    final_rows = []
    for item_id, lst in by_item.items():
        js = [Judgement(d.decision, d.labels, d.arkts_score, d.quality_score, d.confidence, d.rationale) for d in lst]
        J = consensus(js)
        
        # Get original item data from first result
        original_data = all_results[0] if all_results else {}
        for r_dict in all_results:
            if r_dict.get("item_id") == item_id:
                original_data = r_dict
                break
        
        final_rows.append({
            "item_id": item_id,
            "final_decision": J.decision,
            "final_labels": J.labels,
            "final_arkts_score": round(J.arkts_score, 3),
            "final_quality_score": round(J.quality_score, 3),
            "final_confidence": round(J.confidence, 3),
            "rationale_sample": J.rationale,
            "replicas": len(lst),
            "len_chars": len((original_data.get("text") or "")),
        })
    
    # Write final summary
    write_csv(summary_file, final_rows)
    
    # Print summary statistics
    counts = {"KEEP": 0, "KEEP_WITH_TAG": 0, "REMOVE": 0}
    for r in final_rows:
        counts[r["final_decision"]] += 1
    
    print("=== Final Summary ===")
    print(f"Total items processed: {len(final_rows)}")
    print("Final decisions:", counts)
    print(f"Summary saved to: {summary_file}")

# ----------------------------
# CLI
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="ArkTS Full Data Processing Pipeline (LLM-based) - No Sampling")
    ap.add_argument("--input", type=str, required=True, help="Path to corpus JSONL")
    ap.add_argument("--out-dir", type=str, default="out_full", help="Output directory")
    ap.add_argument("--replicas", type=int, default=2, help="Number of LLM replicas per item")
    ap.add_argument("--model", type=str, default="qwen3-coder-480b-a35b-instruct", help="Model name for OpenAI-compatible API")
    ap.add_argument("--temps", type=str, default="0.1,0.3", help="Comma-separated temperatures, e.g., 0.0,0.2")
    ap.add_argument("--code-field", type=str, default="text", help="Field name containing code text")
    ap.add_argument("--concurrency", type=int, default=8, help="Parallel requests")
    ap.add_argument("--api-key", type=str, default=None, help="API key (or set OPENAI_API_KEY env var)")
    ap.add_argument("--base-url", type=str, default=None, help="Base URL (or set OPENAI_BASE_URL env var)")
    ap.add_argument("--max-tokens", type=int, default=512, help="Max tokens per response")
    ap.add_argument("--timeout", type=int, default=90, help="Request timeout in seconds")
    ap.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    
    args = ap.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    
    out_dir = Path(args.out_dir)
    temps = [float(x.strip()) for x in args.temps.split(",") if x.strip()]
    
    process_full_data(
        input_path=input_path,
        out_dir=out_dir,
        replicas=args.replicas,
        model=args.model,
        temps=temps,
        code_field=args.code_field,
        concurrency=args.concurrency,
        api_key=args.api_key,
        base_url=args.base_url,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main()