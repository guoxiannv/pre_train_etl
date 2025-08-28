#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to convert JSONL files to JSON format
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils import read_jsonl, write_json

def convert_jsonl_to_json(input_file, output_file=None):
    """
    Convert JSONL file to JSON file
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSON file (optional)
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        return
    
    if not input_file.endswith('.jsonl'):
        print(f"Warning: Input file '{input_file}' does not have .jsonl extension")
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.json"
    
    print(f"Converting '{input_file}' to '{output_file}'...")
    
    try:
        # Read JSONL data
        data = read_jsonl(input_file)
        print(f"Read {len(data)} records from JSONL file")
        
        # Write JSON data (utils.write_json uses indent=4 by default)
        write_json(data, output_file)
        print(f"Successfully converted to JSON file: {output_file}")
        
        
    except Exception as e:
        print(f"Error during conversion: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert JSONL files to JSON format')
    parser.add_argument('input_file', help='Input JSONL file path')
    parser.add_argument('-o', '--output', help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    # Convert file
    convert_jsonl_to_json(args.input_file, args.output)

if __name__ == '__main__':
    # If run without arguments, show usage and convert all JSONL files in current directory
    import sys
    
    if len(sys.argv) == 1:
        print("JSONL to JSON Converter")
        print("=" * 50)
        print("Usage: python jsonl_to_json.py <input_file.jsonl> [-o output_file.json]")
        print("")
        print("Options:")
        print("  -o, --output    Output JSON file path")
        print("")
        
        # Find JSONL files in current directory
        current_dir = os.getcwd()
        jsonl_files = [f for f in os.listdir(current_dir) if f.endswith('.jsonl')]
        
        if jsonl_files:
            print(f"Found JSONL files in current directory:")
            for i, file in enumerate(jsonl_files, 1):
                print(f"  {i}. {file}")
            print("")
            
            choice = input("Enter file number to convert (or 'all' for all files): ").strip()
            
            if choice.lower() == 'all':
                for file in jsonl_files:
                    convert_jsonl_to_json(file)
                    print()
            elif choice.isdigit() and 1 <= int(choice) <= len(jsonl_files):
                selected_file = jsonl_files[int(choice) - 1]
                convert_jsonl_to_json(selected_file)
            else:
                print("Invalid choice")
        else:
            print("No JSONL files found in current directory")
    else:
        main()