#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import argparse
import os
from typing import List, Tuple, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import read_jsonl, write_jsonl
from tqdm import tqdm



def sample_and_split_data(data: List[dict[str, Any]], 
                         sample_size: int, 
                         train_ratio: float = 0.8, 
                         val_ratio: float = 0.1, 
                         test_ratio: float = 0.1,
                         seed: int = 42) -> Tuple[List[dict[str, Any]], List[dict[str, Any]], List[dict[str, Any]], List[dict[str, Any]]]:
    """
    Sample specified number of samples from data and split into train/val/test sets by ratio
    
    Args:
        data: Original data list
        sample_size: Number of samples to take
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        seed: Random seed
        
    Returns:
        (all_data_with_split, train_data, val_data, test_data)
    """
    # Set random seed
    random.seed(seed)
    
    # Check if ratios are valid
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError(f"Ratios should sum to 1.0, current sum is {total_ratio}")
    
    # Check if sample size exceeds total data
    if sample_size > len(data):
        print(f"Warning: Sample size {sample_size} exceeds total data {len(data)}, using all data")
        sample_size = len(data)
    
    # Random sampling
    sampled_data = random.sample(data, sample_size)
    
    # Calculate sizes for each set
    train_size = int(sample_size * train_ratio)
    val_size = int(sample_size * val_ratio)
    test_size = sample_size - train_size - val_size  # Ensure correct total
    
    # Add split field to each record
    for i, record in enumerate(sampled_data):
        if i < train_size:
            record['split'] = 'train'
        elif i < train_size + val_size:
            record['split'] = 'valid'
        else:
            record['split'] = 'test'
    
    # Split data for separate files (optional)
    train_data = [record for record in sampled_data if record['split'] == 'train']
    val_data = [record for record in sampled_data if record['split'] == 'valid']
    test_data = [record for record in sampled_data if record['split'] == 'test']
    
    return sampled_data, train_data, val_data, test_data

def main():
    parser = argparse.ArgumentParser(description='Sample data from formatted_starcode_ts_without_tag.jsonl and split')
    parser.add_argument('--sample_size', type=int, default=None, help='Number of samples (use all data if not provided)')
    parser.add_argument('--input_file', type=str, 
                       default='./code_data/ts_data/formatted_starcode_ts_without_tag.jsonl',
                       help='Input file path')
    parser.add_argument('--output_dir', type=str, 
                       default='./code_data/ts_data/sampled_data',
                       help='Output directory')
    parser.add_argument('--train_ratio', type=float, default=0.9, help='Training set ratio')
    parser.add_argument('--val_ratio', type=float, default=0.05, help='Validation set ratio')
    parser.add_argument('--test_ratio', type=float, default=0.05, help='Test set ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--save_split_files', action='store_true', 
                       help='Save separate train/val/test files (default: only save combined file with split field)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} does not exist")
        return
    
    print(f"Starting to process file: {args.input_file}")
    print(f"Sample size: {args.sample_size if args.sample_size is not None else 'all data'}")
    print(f"Random seed: {args.seed}")
    print(f"Split ratios - Train: {args.train_ratio}, Val: {args.val_ratio}, Test: {args.test_ratio}")
    
    # Read data
    print("Reading data...")
    data = read_jsonl(args.input_file)
    print(f"Total original data: {len(data)}")
    
    # Determine sample size
    sample_size = args.sample_size if args.sample_size is not None else len(data)
    print(f"Actual sample size: {sample_size}")
    
    # Sample and split
    print("Sampling and splitting data...")
    all_data_with_split, train_data, val_data, test_data = sample_and_split_data(
        data, sample_size, args.train_ratio, args.val_ratio, args.test_ratio, args.seed
    )
    
    print(f"Split results:")
    print(f"  Training set: {len(train_data)} samples")
    print(f"  Validation set: {len(val_data)} samples")
    print(f"  Test set: {len(test_data)} samples")
    print(f"  Total: {len(train_data) + len(val_data) + len(test_data)} samples")
    
    # Save data
    print("Saving data...")
    input_file_name = os.path.splitext(os.path.basename(args.input_file))[0]
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Always save combined file with split field
    combined_file = os.path.join(args.output_dir, f'{input_file_name}_with_split.jsonl')
    write_jsonl(all_data_with_split, combined_file)
    print(f"Combined data with split field saved to: {combined_file}")
    
    # Optionally save separate files
    if args.save_split_files:
        train_file = os.path.join(args.output_dir, f'{input_file_name}_train.jsonl')
        val_file = os.path.join(args.output_dir, f'{input_file_name}_val.jsonl')
        test_file = os.path.join(args.output_dir, f'{input_file_name}_test.jsonl')
        
        write_jsonl(train_data, train_file)
        write_jsonl(val_data, val_file)
        write_jsonl(test_data, test_file)
        
        print(f"Separate split files saved to:")
        print(f"  Training set: {train_file}")
        print(f"  Validation set: {val_file}")
        print(f"  Test set: {test_file}")
    else:
        print("Separate split files not saved (use --save_split_files to enable)")
    
    print("Done!")

if __name__ == '__main__':
    main()