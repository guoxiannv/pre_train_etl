#!/usr/bin/env python3
"""
专门用于检查JSONL文件中text字段语法错误的脚本
允许3个以内的语法错误，输出详细的语法错误报告
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Tree-sitter相关导入
try:
    import tree_sitter_typescript as tst
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
    print("✅ Tree-sitter可用，将进行语法检查")
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("❌ Tree-sitter不可用，请安装: pip install tree-sitter tree-sitter-typescript")
    sys.exit(1)


def setup_tree_sitter() -> Optional[Parser]:
    """设置Tree-sitter解析器"""
    try:
        tree_sitter_language = Language(tst.language_typescript())
        parser = Parser()
        parser.language = tree_sitter_language
        return parser
    except Exception as e:
        print(f"❌ Tree-sitter设置失败: {e}")
        return None


def normalize_text(text: str) -> str:
    """
    标准化text内容，处理换行符和转义符
    
    Args:
        text: 原始text内容
        
    Returns:
        标准化后的text内容
    """
    if not text or not isinstance(text, str):
        return ""
    
    try:
        # 处理转义字符
        normalized = text
        
        # 处理常见的转义序列
        escape_mappings = {
            r'\\n': '\n',      # 双反斜杠n -> 换行符
            r'\\t': '\t',      # 双反斜杠t -> 制表符
            r'\\r': '\r',      # 双反斜杠r -> 回车符
            r'\\"': '"',       # 双反斜杠引号 -> 引号
            r"\\'": "'",       # 双反斜杠单引号 -> 单引号
            r'\\\\': '\\',     # 双反斜杠 -> 单反斜杠
        }
        
        for escaped, unescaped in escape_mappings.items():
            normalized = normalized.replace(escaped, unescaped)
        
        # 处理其他可能的转义序列
        normalized = re.sub(r'\\(.)', r'\1', normalized)
        
        # 标准化换行符
        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除首尾空白
        normalized = normalized.strip()
        
        return normalized
        
    except Exception as e:
        print(f"文本标准化过程中发生错误: {e}")
        return text


def check_arkts_syntax(text: str, parser: Parser) -> Tuple[bool, int, int, int]:
    """
    使用Tree-sitter检查ArkTS/TypeScript语法
    
    Args:
        text: 要检查的代码文本
        parser: Tree-sitter解析器
        
    Returns:
        (is_valid, error_count, missing_count, total_nodes)
    """
    if not parser or not text or not isinstance(text, str):
        return True, 0, 0, 0
    
    try:
        # 解析代码
        tree = parser.parse(bytes(text, "utf8"))
        root = tree.root_node
        
        if root is None:
            return False, 0, 0, 0
        
        error_count = 0
        missing_count = 0
        total_nodes = 0
        
        # DFS遍历语法树
        stack = [root]
        while stack:
            node = stack.pop()
            total_nodes += 1
            
            # 检查ERROR节点
            if node.type == "ERROR":
                error_count += 1
            
            # 检查缺失节点
            if node.is_missing:
                missing_count += 1
            
            # 添加子节点到栈中
            stack.extend(node.children)
        
        # 判断语法是否正确（允许3个以内的错误）
        is_valid = error_count <= 3 and missing_count == 0
        
        return is_valid, error_count, missing_count, total_nodes
        
    except Exception as e:
        print(f"语法检查过程中发生错误: {e}")
        return False, 0, 0, 0


def process_jsonl_file(input_file: str, output_dir: str) -> dict:
    """
    处理JSONL文件，检查text字段的语法错误，根据错误数量分类输出
    
    Args:
        input_file: 输入JSONL文件路径
        output_dir: 输出目录路径
        
    Returns:
        处理统计信息字典
    """
    print(f"开始处理文件: {input_file}")
    
    # 设置Tree-sitter
    parser = setup_tree_sitter()
    if not parser:
        print("❌ Tree-sitter设置失败，无法继续")
        return {'total': 0, 'valid': 0, 'minor_errors': 0, 'major_errors': 0}
    
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
        return {'total': 0, 'valid': 0, 'minor_errors': 0, 'major_errors': 0}
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return {'total': 0, 'valid': 0, 'minor_errors': 0, 'major_errors': 0}
    
    # 分类存储记录
    valid_records = []      # 无语法错误
    minor_error_records = []  # 语法错误少于3条
    major_error_records = []  # 语法错误超过3条
    error_details = []      # 错误详情
    
    # 处理每条记录
    for i, record in enumerate(data):
        if 'text' not in record:
            print(f"警告：第 {i+1} 条记录缺少 'text' 字段")
            # 缺少text字段的记录归类到major_errors
            major_error_records.append(record)
            error_details.append({
                'id': record.get('id', f'record_{i+1}'),
                'corpusid': record.get('corpusid', ''),
                'error_count': 0,
                'missing_count': 0,
                'total_nodes': 0,
                'error_type': '缺少text字段',
                'text_preview': ''
            })
            continue
        
        # 标准化text内容
        original_text = record['text']
        normalized_text = normalize_text(original_text)
        record['normalized_text'] = normalized_text
        
        # 语法检查
        if normalized_text:
            is_valid, error_count, missing_count, total_nodes = check_arkts_syntax(normalized_text, parser)
            
            record['syntax_valid'] = is_valid
            record['syntax_errors'] = error_count
            record['syntax_missing'] = missing_count
            record['total_nodes'] = total_nodes
            
            if is_valid:
                valid_records.append(record)
                record['error_details'] = "语法正确"
            else:
                if error_count <= 3:
                    # 语法错误少于等于3条
                    minor_error_records.append(record)
                    record['error_details'] = f"轻微语法错误: {error_count}个错误节点, {missing_count}个缺失节点"
                else:
                    # 语法错误超过3条
                    major_error_records.append(record)
                    record['error_details'] = f"严重语法错误: {error_count}个错误节点, {missing_count}个缺失节点"
                
                # 收集错误记录详情
                error_details.append({
                    'id': record.get('id', f'record_{i+1}'),
                    'corpusid': record.get('corpusid', ''),
                    'error_count': error_count,
                    'missing_count': missing_count,
                    'total_nodes': total_nodes,
                    'error_type': '语法错误',
                    'text_preview': normalized_text[:200] + "..." if len(normalized_text) > 200 else normalized_text
                })
        else:
            # text字段为空
            major_error_records.append(record)
            record['syntax_valid'] = False
            record['syntax_errors'] = 0
            record['syntax_missing'] = 0
            record['total_nodes'] = 0
            record['error_details'] = "text字段为空"
            error_details.append({
                'id': record.get('id', f'record_{i+1}'),
                'corpusid': record.get('corpusid', ''),
                'error_count': 0,
                'missing_count': 0,
                'total_nodes': 0,
                'error_type': 'text字段为空',
                'text_preview': ''
            })
        
        if (i + 1) % 100 == 0:
            print(f"已处理 {i + 1}/{len(data)} 条记录")
    
    # 生成输出文件名
    input_path = Path(input_file)
    base_name = input_path.stem
    
    # 保存无语法错误的记录
    if valid_records:
        valid_file = Path(output_dir) / f"{base_name}_valid.jsonl"
        try:
            with open(valid_file, 'w', encoding='utf-8') as f:
                for record in valid_records:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ 无语法错误记录已保存到: {valid_file}")
        except Exception as e:
            print(f"❌ 保存无语法错误记录失败: {e}")
    
    # 保存轻微语法错误的记录
    if minor_error_records:
        minor_error_file = Path(output_dir) / f"{base_name}_minor_errors.jsonl"
        try:
            with open(minor_error_file, 'w', encoding='utf-8') as f:
                for record in minor_error_records:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ 轻微语法错误记录已保存到: {minor_error_file}")
        except Exception as e:
            print(f"❌ 保存轻微语法错误记录失败: {e}")
    
    # 保存严重语法错误的记录
    if major_error_records:
        major_error_file = Path(output_dir) / f"{base_name}_major_errors.jsonl"
        try:
            with open(major_error_file, 'w', encoding='utf-8') as f:
                for record in major_error_records:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ 严重语法错误记录已保存到: {major_error_file}")
        except Exception as e:
            print(f"❌ 保存严重语法错误记录失败: {e}")
    
    # 生成错误详情报告
    if error_details:
        error_report_file = Path(output_dir) / f"{base_name}_error_details.jsonl"
        try:
            with open(error_report_file, 'w', encoding='utf-8') as f:
                for error in error_details:
                    json.dump(error, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ 错误详情报告已保存到: {error_report_file}")
        except Exception as e:
            print(f"❌ 生成错误详情报告失败: {e}")
    
    # 统计信息
    stats = {
        'total': len(data),
        'valid': len(valid_records),
        'minor_errors': len(minor_error_records),
        'major_errors': len(major_error_records)
    }
    
    # 输出统计信息
    print(f"\n🎯 处理完成！")
    print(f"总记录数: {stats['total']}")
    print(f"无语法错误: {stats['valid']}")
    print(f"轻微语法错误(≤3): {stats['minor_errors']}")
    print(f"严重语法错误(>3): {stats['major_errors']}")
    
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


def batch_syntax_check(input_dir: str, output_dir: str) -> None:
    """
    批量处理trans_text_data文件夹下的所有JSONL文件，进行语法检查
    
    Args:
        input_dir: 输入目录路径（trans_text_data）
        output_dir: 输出目录路径
    """
    print(f"🚀 开始批量语法检查...")
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
        'total_valid': 0,
        'total_minor_errors': 0,
        'total_major_errors': 0
    }
    
    for i, input_file in enumerate(jsonl_files, 1):
        print(f"\n📁 处理文件 {i}/{len(jsonl_files)}: {os.path.basename(input_file)}")
        
        # 处理文件
        stats = process_jsonl_file(input_file, output_dir)
        
        # 累计统计信息
        total_stats['total_records'] += stats['total']
        total_stats['total_valid'] += stats['valid']
        total_stats['total_minor_errors'] += stats['minor_errors']
        total_stats['total_major_errors'] += stats['major_errors']
        
        print(f"✅ 文件处理完成: {os.path.basename(input_file)}")
        print(f"   记录数: {stats['total']}, 有效: {stats['valid']}, 轻微错误: {stats['minor_errors']}, 严重错误: {stats['major_errors']}")
    
    # 输出总体统计信息
    print("\n" + "=" * 60)
    print("🎯 批量语法检查完成！")
    print(f"总文件数: {total_stats['total_files']}")
    print(f"总记录数: {total_stats['total_records']}")
    print(f"总有效记录: {total_stats['total_valid']}")
    print(f"总轻微错误记录: {total_stats['total_minor_errors']}")
    print(f"总严重错误记录: {total_stats['total_major_errors']}")
    print(f"输出目录: {output_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='检查JSONL文件中text字段的语法错误，支持批量处理')
    parser.add_argument('--input-dir', default='trans_text_data', help='输入目录路径（默认: trans_text_data）')
    parser.add_argument('--output-dir', default='syntax_check_results', help='输出目录路径（默认: syntax_check_results）')
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
            print("请确保trans_text_data文件夹存在于脚本同级目录下")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        batch_syntax_check(str(input_dir), str(output_dir))


if __name__ == "__main__":
    main() 