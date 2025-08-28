#!/usr/bin/env python3
"""
调试脚本：检查文件是否存在和可读
"""

import os
import json
from pathlib import Path

def check_file_status(file_path):
    """检查文件状态"""
    print(f"\n📁 检查文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"   ❌ 文件不存在")
        return False
    
    # 检查文件大小
    try:
        file_size = os.path.getsize(file_path)
        print(f"   📏 文件大小: {file_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"   ❌ 无法获取文件大小: {e}")
        return False
    
    # 尝试读取文件前几行
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取前3行
            lines = []
            for i, line in enumerate(f):
                if i >= 3:
                    break
                lines.append(line.strip())
            
            print(f"   📖 前{len(lines)}行内容:")
            for i, line in enumerate(lines):
                if line:
                    print(f"      第{i+1}行: {line[:100]}{'...' if len(line) > 100 else ''}")
                else:
                    print(f"      第{i+1}行: (空行)")
            
            # 尝试解析第一行JSON
            if lines and lines[0]:
                try:
                    first_record = json.loads(lines[0])
                    print(f"   ✅ 第一行JSON解析成功")
                    print(f"   🔑 字段列表: {list(first_record.keys())}")
                    
                    # 检查是否有text字段
                    if 'text' in first_record:
                        print(f"   ✅ 包含 'text' 字段")
                    else:
                        print(f"   ⚠️ 缺少 'text' 字段")
                        # 检查其他可能的字段
                        possible_fields = ['content', 'code', 'llm_formatted']
                        for field in possible_fields:
                            if field in first_record:
                                print(f"   💡 发现替代字段: '{field}'")
                                break
                except json.JSONDecodeError as e:
                    print(f"   ❌ 第一行JSON解析失败: {e}")
                    return False
            else:
                print(f"   ⚠️ 文件为空或第一行为空")
                return False
                
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
        return False
    
    print(f"   ✅ 文件检查通过")
    return True

def main():
    """主函数"""
    # 获取当前脚本所在目录
    curdir = os.path.dirname(__file__)
    print(f"🔍 当前目录: {curdir}")
    
    # 定义要检查的文件列表
    input_files = [
        "../code_data/raw_data/harmony_samples_formated.jsonl",
        "../code_data/cleaned_data/arkui_2k_pretrain_cleaned_formated.jsonl", 
        "../docs_data/pure_code.jsonl",
        "../code_data/raw_data/dz5484.jsonl"
    ]
    
    print("\n" + "="*60)
    print("🔍 开始检查文件状态")
    print("="*60)
    
    valid_files = []
    for file_path in input_files:
        full_path = os.path.join(curdir, file_path)
        if check_file_status(full_path):
            valid_files.append(file_path)
    
    print("\n" + "="*60)
    print("📊 检查结果总结")
    print("="*60)
    print(f"总文件数: {len(input_files)}")
    print(f"有效文件数: {len(valid_files)}")
    print(f"无效文件数: {len(input_files) - len(valid_files)}")
    
    if valid_files:
        print(f"\n✅ 可以处理的文件:")
        for file_path in valid_files:
            print(f"   - {file_path}")
    
    if len(valid_files) < len(input_files):
        print(f"\n❌ 有问题的文件:")
        for file_path in input_files:
            if file_path not in valid_files:
                print(f"   - {file_path}")
        
        print(f"\n💡 建议:")
        print(f"   1. 检查文件路径是否正确")
        print(f"   2. 确认文件是否存在")
        print(f"   3. 检查文件格式是否为有效的JSONL")
        print(f"   4. 确认文件编码为UTF-8")

if __name__ == "__main__":
    main() 