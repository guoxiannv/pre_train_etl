#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: Apply formatting from formatted_data.jsonl to judgements.jsonl.

Features:
1. Read formatted_data.jsonl and extract 'text' and 'llm_formatted'
2. Read judgements.jsonl
3. Match by 'text' and add a new field 'llm_formatted' to kept data
   - If no formatted entry exists, fill 'llm_formatted' with original 'text'
4. Save the updated judgements to an output file
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
# Add the parent directory to sys.path to import utils and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils import read_jsonl, write_jsonl, read_json

def apply_format_data(formatted_data: List[Dict[str, Any]], 
                     kept_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Use 'text' as the matching key and add a new field 'llm_formatted' to kept_data.
    If an item is not found in formatted_data, set 'llm_formatted' to the original 'text'.

    Args:
        formatted_data: list containing formatting information
        kept_data: list to which formatting will be applied

    Returns:
        The updated kept_data list
    """
    # Build a mapping from original 'text' to 'llm_formatted'
    format_info_map = {}
    
    print("构建格式化信息映射（基于text字段）...")
    for item in formatted_data:
        original_text = item.get('text')
        if original_text is not None and 'llm_formatted' in item:
            format_info_map[original_text] = item['llm_formatted']
    
    print(f"找到 {len(format_info_map)} 条有格式化信息的记录")
    
    # Apply formatting information to kept_data
    from_formatted_count = 0
    from_original_count = 0
    updated_data = []
    
    for item in kept_data:
        item_copy = item.copy()
        original_text = item.get('text')
        
        if original_text is not None:
            if original_text in format_info_map:
                item_copy['llm_formatted'] = format_info_map[original_text]
                from_formatted_count += 1
            else:
                item_copy['llm_formatted'] = original_text
                from_original_count += 1
        
        updated_data.append(item_copy)
    
    print(f"成功填充 llm_formatted 字段 {from_formatted_count + from_original_count} 条（来源于formatted_data: {from_formatted_count}，使用原text: {from_original_count}）")
    return updated_data

def main():
    """Main entrypoint"""
    print("🚀 开始应用格式化数据...")
    print("=" * 60)
    
    # File paths
    formatted_data_path = "data_processing/code_data/tagged_data/formatted_data.jsonl"
    kept_data_path = "out_rounds/judgements.jsonl"
    output_path = "out_rounds/judgements_partially_formatted.jsonl"
    
    # Check if files exist
    if not Path(formatted_data_path).exists():
        print(f"错误：formatted_data.jsonl 文件不存在: {formatted_data_path}")
        return
    
    if not Path(kept_data_path).exists():
        print(f"错误：kept_all_with_split.jsonl 文件不存在: {kept_data_path}")
        return
    
    # Read data
    print("1. 读取formatted_data.jsonl...")
    formatted_data = read_jsonl(formatted_data_path)
    if not formatted_data:
        print("错误：无法读取formatted_data.jsonl")
        return
    
    print("2. 读取kept_all_with_split.jsonl...")
    kept_data = read_jsonl(kept_data_path)
    if not kept_data:
        print("错误：无法读取kept_all_with_split.jsonl")
        return
    
    # Apply formatted data
    print("3. 应用格式化信息...")
    updated_data = apply_format_data(formatted_data, kept_data)
    
    # Save updated data (no return check; write_jsonl has no return value)
    print("4. 保存更新后的数据...")
    write_jsonl(updated_data, output_path)
    print(f"\n✅ 格式化数据应用完成！")
    print(f"输出文件: {output_path}")
    print(f"总记录数: {len(updated_data)}")
    
    # Report update statistics
    llm_formatted_count = sum(1 for item in updated_data if 'llm_formatted' in item)
    print(f"包含 llm_formatted 字段的记录数: {llm_formatted_count}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()