#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fim_make_dataset.py

Convert raw JSONL (each line: {"text": "...code..."} or {"code": "..."})
to a FIM dataset JSONL.

- Supported span strategies: function body / line block / identifier region / token window
- Dependencies: pip install tree_sitter tree_sitter_typescript

Usage (eval dataset generation from a single file):
  python FIM.py \
    --input arkts_raw.jsonl \
    --output arkts_fim_eval.jsonl \
    --min_middle_chars 80 --max_middle_chars 1200 \
    --seed 42 --samples 2000

Usage (sample X% to FIM and mix with original for multiple files):
  python FIM.py \
    --inputs a.jsonl b.jsonl \
    --fim_percent 20 \
    --output_dir out_dir \
    --min_middle_chars 80 --max_middle_chars 1200 --seed 42
"""
import json, re, random, argparse, sys
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_typescript as tst

FIM_PREFIX = "<|fim_prefix|>"
FIM_SUFFIX = "<|fim_suffix|>"
FIM_MIDDLE = "<|fim_middle|>"

# ---------- Tree-sitter initialization (TS/ArkTS reuses TypeScript grammar) ----------
tree_sitter_language = Language(tst.language_typescript())
parser = Parser()
parser.language = tree_sitter_language

# ---------- Utilities ----------
IDENT_RE = re.compile(r"[A-Za-z_]\w+")

def safe_slice(s, start, end):
    start = max(0, min(len(s), start))
    end = max(0, min(len(s), end))
    if start > end: start, end = end, start
    return s[start:end], start, end

def choose_span_by_lines(code, min_chars, max_chars, seed):
    lines = code.splitlines(keepends=True)
    if len(lines) < 6: return None
    rnd = random.Random(seed)
    for _ in range(30):
        L = rnd.randint(2, min(20, max(2, len(lines)//3)))
        i = rnd.randint(0, max(0, len(lines)-L))
        mid = "".join(lines[i:i+L])
        if min_chars <= len(mid) <= max_chars and not mid.isspace():
            # compute char offsets
            start = sum(len(x) for x in lines[:i])
            end = start + len(mid)
            return (start, end)
    return None

def tree_nodes(root, types):
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type in types:
            yield n
        for c in n.children:
            stack.append(c)

def choose_span_by_function_block(code, min_chars, max_chars, seed):
    tree = parser.parse(code.encode("utf-8"))
    root = tree.root_node
    func_types = {"function_declaration", "method_definition", "function"}
    block_types = {"statement_block", "block"}
    rnd = random.Random(seed)
    candidates = []
    for f in tree_nodes(root, func_types):
        # find function body
        body = None
        for c in f.children:
            if c.type in block_types:
                body = c
                break
        if not body: 
            continue
        # sample one contiguous span inside the function body
        start, end = body.start_byte, body.end_byte
        if end - start < min_chars: 
            continue
        # sample span length
        for _ in range(10):
            L = rnd.randint(min_chars, min(max_chars, max(min_chars, (end-start)//2)))
            a = rnd.randint(start, max(start, end-L))
            b = a + L
            seg = code.encode("utf-8")[a:b].decode("utf-8", errors="ignore")
            if not seg.isspace():
                # map back to char indices (approximate at UTF-8 boundaries)
                s = len(code.encode("utf-8")[:a].decode("utf-8", errors="ignore"))
                e = s + len(seg)
                candidates.append((s, e))
                break
    if not candidates: 
        return None
    return rnd.choice(candidates)

def choose_span_by_identifier(code, min_chars, max_chars, seed):
    # pick a frequent identifier, then expand around nearby occurrences to form a span
    rnd = random.Random(seed)
    idents = IDENT_RE.findall(code)
    if not idents: 
        return None
    # sort by frequency
    from collections import Counter
    cand = [w for w,c in Counter(idents).most_common(30) if len(w)>1 and not w.isupper()]
    if not cand: 
        return None
    target = rnd.choice(cand[:10])
    spans = [m.span() for m in re.finditer(rf"\b{re.escape(target)}\b", code)]
    if len(spans) < 3: 
        return None
    # choose a central occurrence and expand a few occurrences to both sides to form a contiguous span
    center_idx = rnd.randrange(1, len(spans)-1)
    left = max(0, center_idx - rnd.randint(1, 3))
    right = min(len(spans)-1, center_idx + rnd.randint(1, 3))
    start = spans[left][0]
    end = spans[right][1]
    # relax to token context
    start = max(0, start - rnd.randint(0, 40))
    end = min(len(code), end + rnd.randint(0, 40))
    if min_chars <= (end - start) <= max_chars:
        return (start, end)
    return None

def choose_span_by_tokens(code, min_chars, max_chars, seed):
    rnd = random.Random(seed)
    if len(code) < min_chars: 
        return None
    for _ in range(20):
        L = rnd.randint(min_chars, min(max_chars, max(min_chars, len(code)//3)))
        a = rnd.randint(0, max(0, len(code)-L))
        b = a + L
        if not code[a:b].isspace():
            return (a, b)
    return None

def build_fim_record(code, span):
    s, e = span
    prefix, _, _ = safe_slice(code, 0, s)
    middle, _, _ = safe_slice(code, s, e)
    suffix, _, _ = safe_slice(code, e, len(code))
    fim_text = f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}{middle}"
    return {
        "text": fim_text,
        "meta": {
            "middle_chars": [s, e],
            "prefix_len": len(prefix),
            "suffix_len": len(suffix),
            "middle_len": len(middle)
        }
    }

def pick_span(code, strategy, min_chars, max_chars, seed):
    if strategy == "function":
        return choose_span_by_function_block(code, min_chars, max_chars, seed)
    if strategy == "line":
        return choose_span_by_lines(code, min_chars, max_chars, seed)
    if strategy == "identifier":
        return choose_span_by_identifier(code, min_chars, max_chars, seed)
    if strategy == "token":
        return choose_span_by_tokens(code, min_chars, max_chars, seed)
    return None

def make_fim_dataset(input_path, output_path, samples=2000, 
                     min_middle_chars=80, max_middle_chars=1200, 
                     seed=42, p_function=0.4, p_line=0.3, 
                     p_identifier=0.2, p_token=0.1):
    """
    Convert raw JSONL (each line has `text` or `code`) into a FIM eval JSONL.

    Args:
        input_path: Input JSONL file.
        output_path: Output JSONL file.
        samples: Maximum number of output samples.
        min_middle_chars: Minimum chars for the removed middle span.
        max_middle_chars: Maximum chars for the removed middle span.
        seed: Random seed.
        p_function, p_line, p_identifier, p_token: Sampling probabilities per strategy.

    Returns:
        Number of written samples (int).
    """
    rng = random.Random(seed)
    probs = [
        ("function", p_function),
        ("line", p_line),
        ("identifier", p_identifier),
        ("token", p_token)
    ]
    # normalize probabilities
    z = sum(p for _, p in probs)
    probs = [(k, p / z) for k, p in probs] if z > 0 else probs

    in_path, out_path = Path(input_path), Path(output_path)
    n_written = 0
    with in_path.open("r", encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            if n_written >= samples: break
            try:
                obj = json.loads(line)
            except Exception:
                continue
            base_text = obj.get("text") or obj.get("code") or ""
            lf = obj.get("llm_formatted")
            # resolve llm_formatted text if present
            if isinstance(lf, str):
                llm_text = lf
            elif isinstance(lf, dict):
                llm_text = lf.get("text") or ""
            else:
                llm_text = ""

            # choose a single candidate: prefer llm_formatted if the field exists in the object; otherwise use base text
            selected = llm_text if ("llm_formatted" in obj) else base_text

            # skip if selected is empty or too short to build a valid FIM span
            if not selected or len(selected) < (min_middle_chars + 10):
                continue

            # pick strategy
            r = rng.random()
            acc = 0.0
            strategy = "token"
            for k, p in probs:
                acc += p
                if r <= acc:
                    strategy = k
                    break
            # select span
            span = pick_span(selected, strategy, min_middle_chars, max_middle_chars, rng.randint(0, 10**9))
            if not span:
                continue
            rec = build_fim_record(selected, span)
            rec["meta"]["strategy"] = strategy
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_written += 1

    return n_written

def sample_fim_and_mix_for_file(input_path, output_path, fim_percent=20.0,
                                min_middle_chars=80, max_middle_chars=1200,
                                seed=42, p_function=0.4, p_line=0.3,
                                p_identifier=0.2, p_token=0.1,
                                mix_mode="interleave"):
    """
    For a single JSONL file: randomly sample X% of lines to convert to FIM.
    Two mixing modes are supported:
      - interleave (default): evenly interleave FIM samples with the remaining originals
      - random_replay: keep all original lines (including those converted) and randomly place both originals and FIM samples together

    Each input line should contain `text` or `code`.

    Args:
        input_path: Input JSONL file path.
        output_path: Output JSONL file path (recommend: original_name_{X}FIM.jsonl).
        fim_percent: Sampling percent (0-100).
        mix_mode: "interleave" or "random_replay".
        Other args are the same as FIM span selection parameters.

    Returns:
        Number of written samples (int).
    """
    rng = random.Random(seed)
    probs = [
        ("function", p_function),
        ("line", p_line),
        ("identifier", p_identifier),
        ("token", p_token),
    ]
    z = sum(p for _, p in probs)
    probs = [(k, p / z) for k, p in probs] if z > 0 else probs

    def choose_strategy(local_rng):
        r = local_rng.random()
        acc = 0.0
        for k, p in probs:
            acc += p
            if r <= acc:
                return k
        return probs[-1][0] if probs else "token"

    # read and collect valid items
    # items: List[Tuple[str, Optional[str]]] => (base_text, llm_text)
    items = []
    with Path(input_path).open("r", encoding="utf-8") as fin:
        for line in fin:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            base_text = obj.get("text") or obj.get("code") or ""
            lf = obj.get("llm_formatted")
            if isinstance(lf, str):
                llm_text = lf
            elif isinstance(lf, dict):
                llm_text = lf.get("text")
            else:
                llm_text = None
            if base_text or llm_text:
                items.append((base_text or "", llm_text if isinstance(llm_text, str) else None))

    if not items:
        # still create an empty file
        Path(output_path).write_text("", encoding="utf-8")
        return 0

    total = len(items)
    n_fim_target = max(0, min(total, int(round((fim_percent / 100.0) * total))))

    # choose indices to be converted to FIM
    all_indices = list(range(total))
    fim_indices = set(rng.sample(all_indices, n_fim_target)) if n_fim_target > 0 else set()

    fim_list = []      # List[str] FIM-converted texts (from base and llm_formatted)
    origin_list = []   # List[str] original base texts

    local_rng = random.Random(seed ^ 0xC0FFEE)
    for idx, pair in enumerate(items):
        base_text, llm_text = pair
        # keep original base text always
        if base_text:
            origin_list.append(base_text)
        # if selected, try build FIM for base and llm_formatted
        if idx in fim_indices:
            if base_text and len(base_text) >= (min_middle_chars + 10):
                rec_text = None
                for _ in range(12):
                    strategy = choose_strategy(local_rng)
                    span = pick_span(base_text, strategy, min_middle_chars, max_middle_chars, local_rng.randint(0, 10**9))
                    if span:
                        rec = build_fim_record(base_text, span)
                        rec_text = rec["text"]
                        break
                if rec_text:
                    fim_list.append(rec_text)
            if llm_text and len(llm_text) >= (min_middle_chars + 10):
                rec_text_2 = None
                for _ in range(12):
                    strategy = choose_strategy(local_rng)
                    span = pick_span(llm_text, strategy, min_middle_chars, max_middle_chars, local_rng.randint(0, 10**9))
                    if span:
                        rec2 = build_fim_record(llm_text, span)
                        rec_text_2 = rec2["text"]
                        break
                if rec_text_2:
                    fim_list.append(rec_text_2)

    # build final list according to mix_mode
    mixed = []
    if mix_mode == "random_replay":
        # keep all originals (already in origin_list) and add all FIMs; then shuffle
        mixed = [*origin_list, *fim_list]
        rng_shuffle = random.Random(seed ^ 0xA5A5)
        rng_shuffle.shuffle(mixed)
    else:
        # interleave proportionally (instead of concatenation or pure shuffle)
        i = j = 0
        len_f, len_o = len(fim_list), len(origin_list)
        if len_f == 0 or len_o == 0:
            mixed = [*fim_list, *origin_list]
        else:
            while i < len_f or j < len_o:
                prog_f = (i / len_f) if len_f else 1.0
                prog_o = (j / len_o) if len_o else 1.0
                if i < len_f and (prog_f <= prog_o or j >= len_o):
                    mixed.append(fim_list[i])
                    i += 1
                elif j < len_o:
                    mixed.append(origin_list[j])
                    j += 1

    # write out
    n_written = 0
    with Path(output_path).open("w", encoding="utf-8") as fout:
        for txt in mixed:
            fout.write(json.dumps({"text": txt}, ensure_ascii=False) + "\n")
            n_written += 1

    return n_written

def main():
    ap = argparse.ArgumentParser()
    # Mode 1: existing eval dataset construction
    ap.add_argument("--input")
    ap.add_argument("--output")
    ap.add_argument("--samples", type=int, default=2000)
    ap.add_argument("--min_middle_chars", type=int, default=80)
    ap.add_argument("--max_middle_chars", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=42)
    # strategy probabilities
    ap.add_argument("--p_function", type=float, default=0.4)
    ap.add_argument("--p_line", type=float, default=0.3)
    ap.add_argument("--p_identifier", type=float, default=0.2)
    ap.add_argument("--p_token", type=float, default=0.1)
    # Mode 2: sample X% to FIM per file and mix with the rest
    ap.add_argument("--inputs", nargs="+", help="List of input JSONL files")
    ap.add_argument("--fim_percent", type=float, default=None, help="Percent per file to convert to FIM (0-100)")
    ap.add_argument("--output_dir", default=None, help="Output directory (defaults to each input's directory)")
    ap.add_argument("--out_ext", default=".jsonl", help="Output file extension, default .jsonl")
    ap.add_argument("--mix_mode", choices=["interleave", "random_replay"], default="interleave", help="Mixing strategy for outputs")
    args = ap.parse_args()

    # Branch: if --inputs and --fim_percent are provided, run sampling+mix mode
    if args.inputs and args.fim_percent is not None:
        total_written = 0
        for in_path_str in args.inputs:
            in_path = Path(in_path_str)
            parent = Path(args.output_dir) if args.output_dir else in_path.parent
            percent_tag = f"{int(round(args.fim_percent))}FIM"
            stem = in_path.stem  # e.g. file.jsonl -> file
            out_name = f"{stem}_{percent_tag}{args.out_ext}"
            out_path = parent / out_name
            n = sample_fim_and_mix_for_file(
                input_path=str(in_path),
                output_path=str(out_path),
                fim_percent=float(args.fim_percent),
                min_middle_chars=args.min_middle_chars,
                max_middle_chars=args.max_middle_chars,
                seed=args.seed,
                p_function=args.p_function,
                p_line=args.p_line,
                p_identifier=args.p_identifier,
                p_token=args.p_token,
                mix_mode=args.mix_mode,
            )
            print(f"[OK] {in_path} -> {out_path} (written: {n})")
            total_written += n
        print(f"[DONE] processed {len(args.inputs)} files, total samples: {total_written}")
        return

    # Otherwise, fallback to eval dataset construction mode (require --input and --output)
    if not args.input or not args.output:
        print("Error: either provide --inputs with --fim_percent, or provide --input and --output.", file=sys.stderr)
        sys.exit(2)

    n_written = make_fim_dataset(
        input_path=args.input,
        output_path=args.output,
        samples=args.samples,
        min_middle_chars=args.min_middle_chars,
        max_middle_chars=args.max_middle_chars,
        seed=args.seed,
        p_function=args.p_function,
        p_line=args.p_line,
        p_identifier=args.p_identifier,
        p_token=args.p_token,
    )

    print(f"[OK] wrote {n_written} FIM eval samples to {args.output}")

if __name__ == "__main__":
    main()
