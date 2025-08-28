#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mix_jsonl_fixed.py  –  Keep all ArkTS, sample just enough TS, then shuffle.

Example
-------
# Produce a corpus that is 70 % ArkTS, 30 % TS
python mix_jsonl_fixed.py arkts.jsonl ts.jsonl mixed.jsonl \
       --arkts_ratio 0.7 --seed 2025
"""
import argparse, itertools, json, os, random, sys
from pathlib import Path
from typing import List

# --------------------------------------------------------------------------- #
def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)

def reservoir_sample(path: Path, k: int, *, seed: int) -> List[str]:
    """Return `k` random lines from `path` (k may be 0)."""
    rng = random.Random(seed)
    sample: List[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i < k:                                   # fill initial bucket
                sample.append(line)
            else:
                j = rng.randrange(i + 1)               # inclusive upper bound
                if j < k:
                    sample[j] = line
    return sample

def streaming_block_shuffle(it, *, rng: random.Random, block=100_000):
    """Yield items from iterator `it` in roughly-shuffled order, block by block."""
    buf: List[str] = []
    for item in it:
        buf.append(item)
        if len(buf) >= block:
            rng.shuffle(buf)
            yield from buf
            buf.clear()
    if buf:
        rng.shuffle(buf)
        yield from buf

# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Mix ArkTS with a sampled slice of"
                                             " TS to achieve a target ratio.")
    ap.add_argument("arkts",  type=Path, help="ArkTS jsonl file")
    ap.add_argument("ts",     type=Path, help="TypeScript jsonl file")
    ap.add_argument("output", type=Path, help="Destination mixed jsonl file")
    ap.add_argument("--arkts_ratio", type=float, default=0.8,
                    help="Fraction of ArkTS lines in final mix (0–1, default 0.7)")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for deterministic sampling/shuffling")
    args = ap.parse_args()

    if not (0.0 < args.arkts_ratio < 1.0):
        sys.exit("arkts_ratio must be in the open interval (0, 1).")

    rng = random.Random(args.seed)

    # 1) Count ArkTS lines and compute how many TS lines we need
    n_arkts = count_lines(args.arkts)
    n_total  = int(round(n_arkts / args.arkts_ratio))
    n_ts_needed = max(n_total - n_arkts, 0)

    # 2) Reservoir-sample the TypeScript file
    ts_sample = reservoir_sample(args.ts, n_ts_needed, seed=args.seed + 1)
    if len(ts_sample) < n_ts_needed:
        print(f"[warn] TS file has only {len(ts_sample)} lines; "
              f"final ArkTS share will be higher than requested.", file=sys.stderr)

    # 3) Write ArkTS + sampled TS, fully shuffled in streaming blocks
    with args.output.open("w", encoding="utf-8") as out,\
         args.arkts.open("r", encoding="utf-8") as ark_fh:
        # Chain ArkTS iterator with list of sampled TS lines
        chain_it = itertools.chain(ark_fh, ts_sample)
        for line in streaming_block_shuffle(chain_it, rng=rng):
            out.write(line)

    print(f"✓ Mixed dataset written to {args.output} "
          f"({n_arkts} ArkTS + {len(ts_sample)} TS)")

if __name__ == "__main__":
    main()
