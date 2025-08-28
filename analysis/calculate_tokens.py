#!/usr/bin/env python3
"""
Script to calculate tokens in the 'text' field of JSONL files
using Qwen2.5-Coder-7B tokenizer from transformers.
Adds a 'text_tokens' field to each entry with the token count.
"""

import json
import os
from pathlib import Path
from transformers import AutoTokenizer
from tqdm import tqdm
from typing import List, Dict, Any, Tuple, Union

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
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                "Qwen/Qwen2.5-Coder-7B",
                trust_remote_code=True
            )
            print("Tokenizer loaded successfully without proxy!")
            return tokenizer
        except Exception as e2:
            print(f"Failed to load tokenizer: {e2}")
            return None

def process_jsonl_with_tokens(input_file_path: str, output_file_path: str, tokenizer) -> Tuple[int, int, int]:
    """
    Process JSONL file and add text_tokens field to each entry.
    
    Args:
        input_file_path: Path to input JSONL file
        output_file_path: Path to output JSONL file with added text_tokens
        tokenizer: Loaded tokenizer instance
    
    Returns:
        Tuple of (total_tokens, total_entries, empty_text_count)
    """
    if tokenizer is None:
        raise ValueError("Tokenizer is not loaded")
    
    total_tokens = 0
    total_entries = 0
    empty_text_count = 0
    
    print(f"Processing file: {input_file_path}")
    
    # First pass to count total lines for progress bar
    with open(input_file_path, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    # Second pass to process and add token counts
    with open(input_file_path, 'r', encoding='utf-8') as input_f, \
         open(output_file_path, 'w', encoding='utf-8') as output_f:
        
        for line_num, line in enumerate(tqdm(input_f, total=total_lines, desc="Processing entries"), 1):
            try:
                data = json.loads(line.strip())
                text_content = data.get('text', '')
                
                if text_content:
                    # Tokenize the text content
                    tokens = tokenizer.encode(text_content)
                    token_count = len(tokens)
                    total_tokens += token_count
                    
                    # Add text_tokens field
                    data['text_tokens'] = token_count
                else:
                    empty_text_count += 1
                    data['text_tokens'] = 0
                
                total_entries += 1
                
                # Write modified data to output file
                json.dump(data, output_f, ensure_ascii=False)
                output_f.write('\n')
                
                # Print progress every 100 entries
                if line_num % 100 == 0:
                    print(f"Processed {line_num} entries, current total tokens: {total_tokens:,}")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue
    
    return total_tokens, total_entries, empty_text_count

def calculate_tokens_for_jsonl(input_file_path: str, output_file_path: Union[str, None] = None) -> Dict[str, Any]:
    """
    External callable function to process JSONL file and add token counts.
    
    Args:
        input_file_path: Path to input JSONL file
        output_file_path: Optional path for output file. If None, will auto-generate
    
    Returns:
        Dictionary with processing results and statistics
    """
    # Setup proxy and load tokenizer
    setup_proxy()
    tokenizer = load_tokenizer()
    
    if tokenizer is None:
        return {"error": "Failed to load tokenizer"}
    
    # Generate output path if not provided
    if output_file_path is None:
        input_path = Path(input_file_path)
        output_file_path = str(input_path.parent / f"{input_path.stem}_with_tokens{input_path.suffix}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    try:
        # Process the file
        total_tokens, total_entries, empty_text_count = process_jsonl_with_tokens(
            input_file_path, output_file_path, tokenizer
        )
        
        # Calculate additional statistics
        entries_with_content = total_entries - empty_text_count
        avg_tokens = total_tokens / entries_with_content if entries_with_content > 0 else 0
        
        results = {
            "input_file": input_file_path,
            "output_file": output_file_path,
            "total_entries": total_entries,
            "entries_with_empty_text": empty_text_count,
            "entries_with_content": entries_with_content,
            "total_tokens": total_tokens,
            "average_tokens_per_entry": round(avg_tokens, 2),
            "success": True
        }
        
        return results
        
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate tokens for JSONL files and add text_tokens field")
    parser.add_argument("input_file", help="Path to input JSONL file")
    parser.add_argument("-o", "--output", help="Path to output file (optional)")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy settings")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found!")
        return
    
    # Disable proxy if requested
    if args.no_proxy:
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
    
    # Process the file
    results = calculate_tokens_for_jsonl(args.input_file, args.output)
    
    if results.get("success"):
        # Print results
        print("\n" + "="*50)
        print("TOKEN CALCULATION RESULTS")
        print("="*50)
        print(f"Input file: {results['input_file']}")
        print(f"Output file: {results['output_file']}")
        print(f"Total entries processed: {results['total_entries']:,}")
        print(f"Entries with empty text: {results['entries_with_empty_text']:,}")
        print(f"Entries with content: {results['entries_with_content']:,}")
        print(f"Total tokens in 'text' field: {results['total_tokens']:,}")
        print(f"Average tokens per non-empty entry: {results['average_tokens_per_entry']}")
        print("="*50)
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()