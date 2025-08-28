#!/usr/bin/env python3
"""
Script to analyze token distribution in code examples and filter by token count ranges.
Processes large files in a streaming fashion.
"""

import json
import os
from transformers import AutoTokenizer
from tqdm import tqdm

def setup_proxy():
    """Setup proxy for model downloading if needed"""
    # Set proxy environment variables
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10809'
    print("Proxy settings configured for model download")

def load_tokenizer():
    """Load Qwen2.5-Coder-7B tokenizer with proxy support"""
    try:
        print("Loading Qwen2.5-Coder-7B tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-Coder-7B",
            trust_remote_code=True,
            proxies={
                'http': 'http://127.0.0.1:10809',
                'https': 'http://127.0.0.1:10809'
            }
        )
        print("Tokenizer loaded successfully!")
        return tokenizer
    except Exception as e:
        print(f"Error loading tokenizer: {e}")
        print("Trying without proxy...")
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-Coder-7B",
            trust_remote_code=True
        )
        return tokenizer

def process_first_n_examples(file_path, tokenizer, n=10):
    """Process first n examples to calculate token/character ratio"""
    total_tokens = 0
    total_chars = 0
    processed_count = 0
    
    print(f"Processing first {n} examples from {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(tqdm(f, total=n, desc="Processing examples")):
            if i >= n:
                break
                
            try:
                example = json.loads(line.strip())
                text_content = example.get('text', '')
                
                if text_content:
                    # Tokenize the text content
                    tokens = tokenizer.encode(text_content)
                    token_count = len(tokens)
                    total_tokens += token_count
                    total_chars += len(text_content)
                    processed_count += 1
            except Exception as e:
                print(f"Error processing example {i}: {e}")
                continue
    
    return total_tokens, total_chars, processed_count

def filter_examples_by_token_range(input_file, output_files, tokenizer, token_ranges):
    """
    Filter examples by token count ranges and save to separate files.
    
    Args:
        input_file: Path to input JSONL file
        output_files: Dictionary mapping range names to output file paths
        tokenizer: Loaded tokenizer
        token_ranges: Dictionary mapping range names to (min_tokens, max_tokens) tuples
    """
    # Initialize file handles for output files
    file_handles = {}
    example_counts = {}
    
    for range_name in token_ranges:
        file_handles[range_name] = open(output_files[range_name], 'w', encoding='utf-8')
        example_counts[range_name] = 0
    
    try:
        # Count total lines for progress bar
        with open(input_file, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        
        print(f"Filtering examples from {input_file}...")
        
        # Process all examples
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Filtering examples"):
                try:
                    example = json.loads(line.strip())
                    text_content = example.get('text', '')
                    
                    if text_content:
                        # Tokenize the text content
                        tokens = tokenizer.encode(text_content)
                        token_count = len(tokens)
                        
                        # Check which ranges this example fits into
                        for range_name, (min_tokens, max_tokens) in token_ranges.items():
                            if min_tokens <= token_count <= max_tokens:
                                # Write to the corresponding output file
                                file_handles[range_name].write(json.dumps(example, ensure_ascii=False) + '\n')
                                example_counts[range_name] += 1
                except Exception as e:
                    print(f"Error processing example: {e}")
                    continue
                    
    finally:
        # Close all file handles
        for range_name, handle in file_handles.items():
            handle.close()
            print(f"Saved {example_counts[range_name]} examples to {output_files[range_name]}")

def main():
    """Main function"""
    # Setup proxy
    setup_proxy()
    
    # Load tokenizer
    tokenizer = load_tokenizer()
    
    # File paths
    input_file = "code_data/cleaned_data/test.jsonl"
    output_file_3k = "code_data/cleaned_data/examples_2.8k-3.2k.jsonl"
    output_file_6k = "code_data/cleaned_data/examples_5.8k-6.2k.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found!")
        return
    
    # Process first 10 examples to calculate token/character ratio
    total_tokens, total_chars, processed_count = process_first_n_examples(input_file, tokenizer, 10)
    
    print("\n" + "="*50)
    print("TOKEN ANALYSIS RESULTS")
    print("="*50)
    print(f"First {processed_count} examples:")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total characters: {total_chars:,}")
    
    if total_tokens > 0:
        chars_per_1000_tokens = (total_chars / total_tokens) * 1000
        print(f"Characters per 1000 tokens: {chars_per_1000_tokens:.2f}")
    
    # Define token ranges
    token_ranges = {
        "3k": (2800, 3200),
        "6k": (5800, 6200)
    }
    
    # Define output files
    output_files = {
        "3k": output_file_3k,
        "6k": output_file_6k
    }
    
    # Filter examples by token ranges
    filter_examples_by_token_range(input_file, output_files, tokenizer, token_ranges)
    
    # Select 5 examples from each file and create final output files
    print("\nSelecting 5 examples from each range...")
    
    # Process 3k range
    selected_3k_file = "code_data/cleaned_data/selected_2.8k-3.2k.jsonl"
    count_3k = 0
    with open(output_file_3k, 'r', encoding='utf-8') as infile, \
         open(selected_3k_file, 'w', encoding='utf-8') as outfile:
        for i, line in enumerate(infile):
            if i >= 5:  # Only take first 5
                break
            outfile.write(line)
            count_3k += 1
    
    # Process 6k range
    selected_6k_file = "code_data/cleaned_data/selected_5.8k-6.2k.jsonl"
    count_6k = 0
    with open(output_file_6k, 'r', encoding='utf-8') as infile, \
         open(selected_6k_file, 'w', encoding='utf-8') as outfile:
        for i, line in enumerate(infile):
            if i >= 5:  # Only take first 5
                break
            outfile.write(line)
            count_6k += 1
    
    print(f"Selected {count_3k} examples for 2.8k-3.2k range: {selected_3k_file}")
    print(f"Selected {count_6k} examples for 5.8k-6.2k range: {selected_6k_file}")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()