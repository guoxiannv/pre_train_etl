#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据kept_all_with_split.jsonl中的split字段将数据分为四个部分
"""

import json
import os
from pathlib import Path

def split_data_by_field():
    """根据split字段将数据分为四个部分"""
    
    # 输入文件路径
    input_file = Path("D:/Documents/PythonProject/pretrain_etl/data_processing/code_data/tagged_data/kept_all_with_split.jsonl")
    
    # 输出目录
    output_dir = Path(".")
    output_dir.mkdir(exist_ok=True)
    
    # 初始化四个数据列表
    train_data = []
    unused_data = []
    valid_data = []
    test_data = []
    
    # 统计信息
    stats = {
        "train": 0,
        "unused": 0,
        "valid": 0,
        "test": 0,
        "total": 0
    }
    
    print(f"正在读取文件: {input_file}")
    
    # 读取并处理数据
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                split_value = data.get("split", "").lower()
                stats["total"] += 1
                
                # 根据split字段分类
                if split_value == "train":
                    train_data.append(data)
                    stats["train"] += 1
                elif split_value == "unused":
                    unused_data.append(data)
                    stats["unused"] += 1
                elif split_value == "valid":
                    valid_data.append(data)
                    stats["valid"] += 1
                elif split_value == "test":
                    test_data.append(data)
                    stats["test"] += 1
                else:
                    print(f"警告: 第{line_num}行有未知的split值: {split_value}")
                
                # 每1000行打印一次进度
                if line_num % 1000 == 0:
                    print(f"已处理 {line_num} 行...")
                    
            except json.JSONDecodeError as e:
                print(f"错误: 第{line_num}行JSON解析失败: {e}")
                continue
    
    print(f"\n数据读取完成，统计信息:")
    print(f"总数据量: {stats['total']}")
    print(f"train: {stats['train']}")
    print(f"unused: {stats['unused']}")
    print(f"valid: {stats['valid']}")
    print(f"test: {stats['test']}")
    
    # 保存分类后的数据
    output_files = {
        "L2R_train": train_data,
        "L2R_unused": unused_data,
        "L2R_valid": valid_data,
        "L2R_test": test_data
    }
    
    print("\n正在保存分类后的数据...")
    
    for filename, data_list in output_files.items():
        if data_list:
            output_file = output_dir / f"{filename}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in data_list:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"已保存 {filename}.jsonl，包含 {len(data_list)} 条数据")
        else:
            print(f"警告: {filename} 没有数据")
    
    # 保存统计信息
    stats_file = output_dir / "split_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n统计信息已保存到: {stats_file}")
    
    print("\n数据分割完成！")

if __name__ == "__main__":
    split_data_by_field()
