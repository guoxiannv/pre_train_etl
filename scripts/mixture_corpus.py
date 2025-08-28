#!/usr/bin/env python3
"""
Script to evenly distribute records from A.jsonl into B.jsonl by splitting both
into n blocks, merging corresponding blocks, shuffling, and writing out the result.
"""
import random
import argparse
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import read_jsonl, write_jsonl


def split_list(lst, n):
    """
    Split list lst into n roughly equal parts (first parts get the extra items).
    Yields n lists whose concatenation is lst.
    """
    k, m = divmod(len(lst), n)
    for i in range(n):
        start = i * k + min(i, m)
        end = start + k + (1 if i < m else 0)
        yield lst[start:end]


def main():
    parser = argparse.ArgumentParser(
        description="Distribute auxiliary corpus into main corpus evenly across n blocks"
    )
    parser.add_argument(
        "--main_corpus", required=True, help="Path to main corpus JSONL file (base records)"
    )
    parser.add_argument(
        "--aux_corpus", required=True, help="Path to auxiliary corpus JSONL file (records to distribute)"
    )
    parser.add_argument(
        "--output", required=True, help="Output path for merged JSONL"
    )
    parser.add_argument(
        "--n", type=int, default=128, help="Number of blocks to split into"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Optional random seed for reproducibility"
    )
    parser.add_argument(
        "--ratio", type=float, default=None, help="Ratio of main corpus records to use relative to auxiliary corpus records (e.g., 0.2 for 20%)"
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Load records
    main_items = read_jsonl(args.main_corpus)
    aux_items = read_jsonl(args.aux_corpus)
    
    print(f"Main corpus total records: {len(main_items)}")
    print(f"Auxiliary corpus total records: {len(aux_items)}")
    
    # Apply ratio if specified
    if args.ratio is not None:
        if args.ratio <= 0 or args.ratio > 1:
            parser.error("Ratio must be between 0 and 1 (exclusive of 0, inclusive of 1).")
        
        target_main_count = int(len(aux_items) * args.ratio)
        if target_main_count > len(main_items):
            print(f"Warning: Requested {target_main_count} main corpus records (aux count * {args.ratio}), but only {len(main_items)} available. Using all main corpus records.")
        else:
            main_items = main_items[:target_main_count]
            print(f"Using {len(main_items)} main corpus records ({args.ratio * 100:.1f}% of auxiliary corpus count)")

    if args.n <= 0:
        parser.error("Number of blocks --n must be positive.")
    if args.n > len(main_items):
        parser.error("--n cannot exceed the number of records in main corpus.")

    # Split into chunks
    aux_chunks = list(split_list(aux_items, args.n))
    main_chunks = list(split_list(main_items, args.n))

    # Merge and shuffle each block
    merged = []
    for idx in range(args.n):
        block = main_chunks[idx] + aux_chunks[idx]
        random.shuffle(block)
        merged.extend(block)

    # Write out merged data
    write_jsonl(merged, args.output)


if __name__ == "__main__":
    main()
