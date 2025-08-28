#!/usr/bin/env python3
"""
拼接JSONL文件中三个字段的脚本
将 above_functions + source_method_code + below_functions 拼接成新的 text 字段
支持批量处理 trans_text_data 文件夹下的所有JSONL文件
为每条记录生成基于filePath的稳定ID
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict


def concatenate_fields(record: Dict) -> str:
    """
    拼接三个字段：above_functions + source_method_code + below_functions
    
    Args:
        record: 包含字段的字典记录
        
    Returns:
        拼接后的text字符串
    """
    # 获取三个字段的值，如果不存在则设为空字符串
    above_functions = record.get('above_functions', '')
    source_method_code = record.get('source_method_code', '')
    below_functions = record.get('below_functions', '')
    
    # 智能处理字段值，转换为合适的字符串，保留原始空格
    def process_field_value(value):
        if value is None:
            return ''
        elif isinstance(value, str):
            # 保留原始空格，不使用strip()
            return value
        elif isinstance(value, (list, tuple)):
            # 如果是列表或元组，且为空，返回空字符串
            if len(value) == 0:
                return ''
            # 如果列表包含字符串元素，用换行符连接，保留每个元素的原始空格
            elif all(isinstance(item, str) for item in value):
                return '\n'.join(item for item in value if item)  # 不使用strip()
            # 其他情况，转换为字符串
            else:
                return str(value)
        elif isinstance(value, dict):
            # 如果是字典，转换为JSON字符串（去除首尾的{}）
            try:
                json_str = json.dumps(value, ensure_ascii=False)
                return json_str[1:-1] if json_str.startswith('{') and json_str.endswith('}') else json_str
            except:
                return str(value)
        else:
            # 其他类型直接转换为字符串
            return str(value)
    
    # 处理三个字段
    above_functions = process_field_value(above_functions)
    source_method_code = process_field_value(source_method_code)
    below_functions = process_field_value(below_functions)
    
    # 直接拼接三个字段，保留原有的空格和换行
    concatenated_text = above_functions + source_method_code + below_functions
    
    return concatenated_text


def generate_stable_id(file_path: str) -> str:
    """
    基于filePath生成稳定的ID
    
    Args:
        file_path: 文件路径字符串
        
    Returns:
        64位十六进制SHA256哈希ID
    """
    if not file_path or not isinstance(file_path, str):
        # 如果没有filePath，生成一个随机ID
        import uuid
        return str(uuid.uuid4())
    
    try:
        # 使用SHA256哈希生成稳定ID
        stable_id = hashlib.sha256(file_path.encode('utf-8')).hexdigest()
        return stable_id
    except Exception as e:
        print(f"生成ID时发生错误: {e}")
        # 出错时生成随机ID
        import uuid
        return str(uuid.uuid4())


def process_jsonl_file(input_file: str, output_dir: str) -> dict:
    """
    处理单个JSONL文件，拼接字段并生成新的text字段
    同时为每条记录生成基于path的稳定ID，并标准化字段名
    
    Args:
        input_file: 输入JSONL文件路径
        output_dir: 输出目录路径
        
    Returns:
        处理统计信息字典
    """
    print(f"开始处理文件: {input_file}")
    
    # 读取数据
    try:
        data = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # 跳过空行
                    continue
                
                try:
                    record = json.loads(line)
                    data.append(record)
                except json.JSONDecodeError as e:
                    print(f"第 {line_num} 行JSON解析失败: {e}")
                    continue
        
        print(f"成功读取 {len(data)} 条记录")
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {input_file}")
        return {'total': 0, 'processed': 0, 'skipped': 0, 'missing_fields': 0, 'id_generated': 0, 'fields_renamed': 0}
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return {'total': 0, 'processed': 0, 'skipped': 0, 'missing_fields': 0, 'id_generated': 0, 'fields_renamed': 0}
    
    # 处理每条记录
    processed_count = 0
    skipped_count = 0
    missing_fields_count = 0
    id_generated_count = 0
    fields_renamed_count = 0
    
    for i, record in enumerate(data):
        # 字段名标准化：将projectName改为project_name，将filePath改为path
        if 'projectName' in record:
            record['project_name'] = record.pop('projectName')
            fields_renamed_count += 1
            print(f"第 {i+1} 条记录：字段名 'projectName' 已改为 'project_name'")
        
        if 'filePath' in record:
            record['path'] = record.pop('filePath')
            fields_renamed_count += 1
            print(f"第 {i+1} 条记录：字段名 'filePath' 已改为 'path'")
        
        # 生成基于path的稳定ID
        file_path = record.get('path', '')
        if file_path:
            record['id'] = generate_stable_id(file_path)
            id_generated_count += 1
            print(f"第 {i+1} 条记录：基于路径 '{file_path}' 生成ID: {record['id'][:8]}...")
        else:
            print(f"警告：第 {i+1} 条记录缺少 'path' 字段，将生成随机ID")
            record['id'] = generate_stable_id("")
            id_generated_count += 1
        
        # 检查是否包含所需的字段
        required_fields = ['above_functions', 'source_method_code', 'below_functions']
        missing_fields = [field for field in required_fields if field not in record]
        
        if missing_fields:
            print(f"警告：第 {i+1} 条记录缺少字段: {missing_fields}")
            record['text'] = ""
            record['concatenation_status'] = f"缺少字段: {', '.join(missing_fields)}"
            missing_fields_count += 1
            continue
        
        # 拼接字段
        try:
            concatenated_text = concatenate_fields(record)
            record['text'] = concatenated_text
            record['concatenation_status'] = "成功拼接"
            processed_count += 1
        except Exception as e:
            print(f"警告：第 {i+1} 条记录拼接失败: {e}")
            record['text'] = ""
            record['concatenation_status'] = f"拼接失败: {str(e)}"
            skipped_count += 1
        
        if (i + 1) % 100 == 0:
            print(f"已处理 {i + 1}/{len(data)} 条记录")
    
    # 生成输出文件名
    input_path = Path(input_file)
    base_name = input_path.stem
    
    # 保存处理后的数据
    output_file = Path(output_dir) / f"{base_name}_concatenated.jsonl"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in data:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        print(f"✅ 处理后的数据已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return {'total': len(data), 'processed': 0, 'skipped': 0, 'missing_fields': 0, 'id_generated': 0}
    
    # 统计信息
    stats = {
        'total': len(data),
        'processed': processed_count,
        'skipped': skipped_count,
        'missing_fields': missing_fields_count,
        'id_generated': id_generated_count,
        'fields_renamed': fields_renamed_count
    }
    
    # 输出统计信息
    print(f"\n🎯 处理完成！")
    print(f"总记录数: {stats['total']}")
    print(f"成功拼接: {stats['processed']}")
    print(f"拼接失败: {stats['skipped']}")
    print(f"缺少字段: {stats['missing_fields']}")
    print(f"生成ID: {stats['id_generated']}")
    print(f"字段重命名: {stats['fields_renamed']}")
    
    return stats


def get_jsonl_files(input_dir: str) -> List[str]:
    """
    获取指定目录下的所有JSONL文件
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        JSONL文件路径列表
    """
    jsonl_files = []
    
    try:
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ 输入目录不存在: {input_dir}")
            return jsonl_files
        
        # 查找所有.jsonl文件
        for file_path in input_path.glob("*.jsonl"):
            jsonl_files.append(str(file_path))
        
        # 也查找.json文件（如果有的话）
        for file_path in input_path.glob("*.json"):
            jsonl_files.append(str(file_path))
        
        print(f"在 {input_dir} 目录下找到 {len(jsonl_files)} 个JSONL文件")
        
    except Exception as e:
        print(f"获取JSONL文件列表时发生错误: {e}")
    
    return jsonl_files


def batch_process_files(input_dir: str, output_dir: str) -> None:
    """
    批量处理bg_data_select文件夹下的所有JSONL文件
    
    Args:
        input_dir: 输入目录路径（bg_data_select）
        output_dir: 输出目录路径
    """
    print(f"🚀 开始批量拼接字段...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 获取所有JSONL文件
    jsonl_files = get_jsonl_files(input_dir)
    
    if not jsonl_files:
        print("❌ 没有找到任何JSONL文件，请检查输入目录")
        return
    
    # 批量处理
    total_stats = {
        'total_files': len(jsonl_files),
        'total_records': 0,
        'total_processed': 0,
        'total_skipped': 0,
        'total_missing_fields': 0,
        'total_id_generated': 0,
        'total_fields_renamed': 0
    }
    
    for i, input_file in enumerate(jsonl_files, 1):
        print(f"\n📁 处理文件 {i}/{len(jsonl_files)}: {os.path.basename(input_file)}")
        
        # 处理文件
        stats = process_jsonl_file(input_file, output_dir)
        
        # 累计统计信息
        total_stats['total_records'] += stats['total']
        total_stats['total_processed'] += stats['processed']
        total_stats['total_skipped'] += stats['skipped']
        total_stats['total_missing_fields'] += stats['missing_fields']
        total_stats['total_id_generated'] += stats['id_generated']
        total_stats['total_fields_renamed'] += stats['fields_renamed']
        
        print(f"✅ 文件处理完成: {os.path.basename(input_file)}")
        print(f"   记录数: {stats['total']}, 成功: {stats['processed']}, 失败: {stats['skipped']}, 缺少字段: {stats['missing_fields']}, 生成ID: {stats['id_generated']}, 字段重命名: {stats['fields_renamed']}")
    
    # 输出总体统计信息
    print("\n" + "=" * 60)
    print("🎯 批量拼接完成！")
    print(f"总文件数: {total_stats['total_files']}")
    print(f"总记录数: {total_stats['total_records']}")
    print(f"总成功拼接: {total_stats['total_processed']}")
    print(f"总拼接失败: {total_stats['total_skipped']}")
    print(f"总缺少字段: {total_stats['total_missing_fields']}")
    print(f"总生成ID: {total_stats['total_id_generated']}")
    print(f"总字段重命名: {total_stats['total_fields_renamed']}")
    print(f"输出目录: {output_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='拼接JSONL文件中的三个字段：above_functions + source_method_code + below_functions，同时生成基于path的稳定ID，并标准化字段名')
    parser.add_argument('--input-dir', default='bg_data_select', help='输入目录路径（默认: bg_data_select）')
    parser.add_argument('--output-dir', default='trans_text_data', help='输出目录路径（默认: trans_text_data）')
    parser.add_argument('--single-file', help='处理单个文件（可选）')
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    curdir = os.path.dirname(__file__)
    
    if args.single_file:
        # 处理单个文件
        if not Path(args.single_file).exists():
            print(f"❌ 文件不存在: {args.single_file}")
            return
        
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = Path(curdir) / output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        stats = process_jsonl_file(args.single_file, str(output_dir))
        
    else:
        # 批量处理
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        
        if not input_dir.is_absolute():
            input_dir = Path(curdir) / input_dir
        
        if not output_dir.is_absolute():
            output_dir = Path(curdir) / output_dir
        
        if not input_dir.exists():
            print(f"❌ 输入目录不存在: {input_dir}")
            print("请确保bg_data_select文件夹存在于脚本同级目录下")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        batch_process_files(str(input_dir), str(output_dir))


if __name__ == "__main__":
    main() 