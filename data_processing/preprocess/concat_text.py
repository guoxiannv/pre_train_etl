#!/usr/bin/env python3
"""
统一文本拼接处理器
合并了两种不同的数据处理逻辑：
1. Fields处理器：拼接 above_functions + source_method_code + below_functions 字段
2. Prompt处理器：从prompt字段中提取三段内容并处理<unused98>标签替换

支持自动检测数据类型或手动指定处理模式
输入：bg_data_select（Fields格式）和 bg_data（Prompt格式）
输出：trans_text_data
"""

import json
import re
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import argparse


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


def extract_text_from_prompt(prompt: str) -> str:
    """
    从prompt中提取三段内容并拼接，保留原有空格格式
    
    Args:
        prompt: 包含三段代码的prompt字符串
        
    Returns:
        拼接后的text字符串
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    
    try:
        # 定义提取模式，保留前后空格
        patterns = {
            'first': r'The context above the method is:\n```arkts\n(.*?)```\n\nAnd here is the code snippet you are asked to complete',
            'second': r'And here is the code snippet you are asked to complete:\n```arkts\n(.*?)```\n\nEnsure that only missing codes',
            'third': r'The context below the method is:\n```arkts\n(.*?)```\n\nThe context above the method is'
        }
        
        extracted_parts = {}
        
        # 提取三段内容，保留原有空格
        for part_name, pattern in patterns.items():
            match = re.search(pattern, prompt, re.DOTALL)
            if match:
                # 不使用strip()，保留原有空格
                extracted_parts[part_name] = match.group(1)
            else:
                extracted_parts[part_name] = ""
        
        # 拼接三段内容，保持原有格式
        combined_text = (
            extracted_parts.get('first', '') + '\n\n' + 
            extracted_parts.get('second', '') + '\n\n' + 
            extracted_parts.get('third', '')
        )
        
        # 只在最后去除首尾的空白行，但保留内容中的空格
        return combined_text.rstrip('\n')
        
    except Exception as e:
        print(f"提取过程中发生错误: {e}")
        return ""


def extract_external_imported(prompt: str) -> str:
    """
    从prompt中提取external_imported信息
    
    Args:
        prompt: prompt字符串
        
    Returns:
        提取的external_imported内容，如果没有找到则返回空字符串
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    
    try:
        # 匹配 "Below are some information from external classes imported by current file:\n```arkts" 到 "```" 之间的内容
        pattern = r'Below are some information from external classes imported by current file:\n```arkts\n(.*?)\n```'
        match = re.search(pattern, prompt, re.DOTALL)
        
        if match:
            # 保留原有空格，不使用strip()
            return match.group(1)
        else:
            return ""
            
    except Exception as e:
        print(f"提取external_imported时发生错误: {e}")
        return ""


def extract_response_code(response: str) -> str:
    """
    从response字段中提取```arkts\n和\n```之间的代码内容，保留空格
    
    Args:
        response: response字段字符串
        
    Returns:
        提取的代码内容
    """
    if not response or not isinstance(response, str):
        return ""
    
    try:
        # 匹配```arkts\n和\n```之间的内容
        pattern = r'```arkts\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            # 保留原有空格，不使用strip()
            return match.group(1)
        else:
            return ""
            
    except Exception as e:
        print(f"提取response代码时发生错误: {e}")
        return ""


def replace_unused98_tags(text: str, response_code: str) -> str:
    """
    将文本中的<unused98>标签替换成response代码，保留空格格式
    
    Args:
        text: 包含<unused98>标签的文本
        response_code: 要替换的代码内容
        
    Returns:
        替换后的文本
    """
    if not text or not isinstance(text, str):
        return text
    
    if not response_code:
        return text
    
    try:
        # 替换所有<unused98>标签
        replaced_text = text.replace('<unused98>', response_code)
        
        return replaced_text
        
    except Exception as e:
        print(f"替换<unused98>标签时发生错误: {e}")
        return text


def generate_stable_id(file_path: str) -> str:
    """
    基于文件路径生成稳定的ID
    
    Args:
        file_path: 文件路径字符串
        
    Returns:
        64位十六进制SHA256哈希ID
    """
    if not file_path or not isinstance(file_path, str):
        # 如果没有路径，生成一个随机ID
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


def extract_project_info_from_repo_url(repo_url: str) -> tuple:
    """
    从repoUrl中提取project_name和path信息
    
    Args:
        repo_url: 仓库URL字符串
        
    Returns:
        (project_name, path) 元组，两者都是repo_name
    """
    if not repo_url or not isinstance(repo_url, str):
        return "", ""
    
    try:
        # 移除.git后缀
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # 分割URL，获取最后一部分
        parts = repo_url.split('/')
        if len(parts) >= 1:
            # 获取最后一部分：repo_name
            repo_name = parts[-1]  # repo_name
            # project_name和path都使用repo_name
            return repo_name, repo_name
        else:
            return "", ""
    except Exception as e:
        print(f"解析repoUrl时发生错误: {e}")
        return "", ""


def detect_data_type(record: Dict) -> str:
    """
    自动检测数据类型（仅用于单个文件处理）
    
    Args:
        record: 数据记录
        
    Returns:
        'fields' 或 'prompt'
    """
    # 检查是否包含fields格式的必需字段
    fields_required = ['above_functions', 'source_method_code', 'below_functions']
    has_fields = all(field in record for field in fields_required)
    
    # 检查是否包含prompt字段
    has_prompt = 'prompt' in record
    
    if has_fields:
        return 'fields'
    elif has_prompt:
        return 'prompt'
    else:
        print(f"警告：无法识别数据类型，记录包含字段: {list(record.keys())}")
        return 'fields'  # 默认返回fields


def safe_json_loads(line: str, line_num: int) -> dict:
    """
    安全地解析JSON行，提供详细的错误信息
    
    Args:
        line: JSON字符串
        line_num: 行号（用于错误报告）
        
    Returns:
        解析后的字典，如果失败返回空字典
    """
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError as e:
        print(f"第 {line_num} 行JSON解析失败: {e}")
        print(f"问题行内容: {line[:100]}...")  # 只显示前100个字符
        return {}
    except Exception as e:
        print(f"第 {line_num} 行处理失败: {e}")
        return {}


def process_fields_record(record: Dict, record_index: int) -> Tuple[bool, Dict]:
    """
    处理Fields格式的记录
    
    Args:
        record: 数据记录
        record_index: 记录索引（用于日志）
        
    Returns:
        (是否成功, 统计信息)
    """
    stats = {
        'processed': 0,
        'skipped': 0,
        'missing_fields': 0,
        'id_generated': 0,
        'fields_renamed': 0
    }
    
    # 字段名标准化：将projectName改为project_name，将filePath改为path
    if 'projectName' in record:
        record['project_name'] = record.pop('projectName')
        stats['fields_renamed'] += 1
    
    if 'filePath' in record:
        record['path'] = record.pop('filePath')
        stats['fields_renamed'] += 1
    
    # 生成基于path的稳定ID
    file_path = record.get('path', '')
    if file_path:
        record['id'] = generate_stable_id(file_path)
        stats['id_generated'] += 1
    else:
        record['id'] = generate_stable_id("")
        stats['id_generated'] += 1
    
    # 检查是否包含所需的字段
    required_fields = ['above_functions', 'source_method_code', 'below_functions']
    missing_fields = [field for field in required_fields if field not in record]
    
    if missing_fields:
        record['text'] = ""
        stats['missing_fields'] += 1
        return False, stats
    
    # 拼接字段
    try:
        concatenated_text = concatenate_fields(record)
        record['text'] = concatenated_text
        stats['processed'] += 1
        return True, stats
    except Exception as e:
        record['text'] = ""
        stats['skipped'] += 1
        return False, stats


def process_prompt_record(record: Dict, record_index: int) -> Tuple[bool, Dict]:
    """
    处理Prompt格式的记录
    
    Args:
        record: 数据记录
        record_index: 记录索引（用于日志）
        
    Returns:
        (是否成功, 统计信息)
    """
    stats = {
        'processed': 0,
        'skipped': 0,
        'unused98_replaced': 0,
        'id_generated': 0,
        'fields_renamed': 0,
        'external_imported_extracted': 0,
        'unused98_not_replaced': 0,
        'unused98_not_replaced_ids': []
    }
    
    if 'prompt' not in record:
        record['text'] = ""
        stats['skipped'] += 1
        return False, stats
    
    # 字段名标准化和字段值处理
    # 1. 处理projectName字段
    if 'projectName' in record:
        # 如果存在projectName，重命名为project_name
        record['project_name'] = record.pop('projectName')
        stats['fields_renamed'] += 1
    elif 'project_name' not in record:
        # 如果既没有projectName也没有project_name，从repoUrl提取
        repo_url = record.get('repoUrl', '')
        if repo_url:
            project_name, _ = extract_project_info_from_repo_url(repo_url)
            if project_name:
                record['project_name'] = project_name
    
    # 2. 处理relativePath字段
    if 'relativePath' in record:
        # 如果存在relativePath，重命名为path
        record['path'] = record.pop('relativePath')
        stats['fields_renamed'] += 1
    elif 'path' not in record:
        # 如果既没有relativePath也没有path，从repoUrl提取
        repo_url = record.get('repoUrl', '')
        if repo_url:
            _, path = extract_project_info_from_repo_url(repo_url)
            if path:
                record['path'] = path
    
    # 生成基于path的稳定ID
    file_path = record.get('path', '')
    if file_path:
        record['id'] = generate_stable_id(file_path)
        stats['id_generated'] += 1
    else:
        record['id'] = generate_stable_id("")
        stats['id_generated'] += 1
    
    # 提取text内容
    text_content = extract_text_from_prompt(record['prompt'])
    record['text'] = text_content
    
    # 提取external_imported内容
    external_imported_content = extract_external_imported(record['prompt'])
    record['external_imported'] = external_imported_content
    if external_imported_content:  # 如果提取到内容，增加计数
        stats['external_imported_extracted'] += 1
    
    stats['processed'] += 1
    
    # 处理<unused98>标签替换
    replacement_failed = False
    if '<unused98>' in text_content:
        if 'response' in record:
            response_code = extract_response_code(record['response'])
            if response_code:
                replaced_text = replace_unused98_tags(text_content, response_code)
                record['text'] = replaced_text
                # 检查是否还有未替换的标签
                if '<unused98>' in replaced_text:
                    stats['unused98_not_replaced'] += 1
                    stats['unused98_not_replaced_ids'].append(record.get('id', 'unknown'))
                    replacement_failed = True
                    print(f"警告：记录ID {record.get('id', 'unknown')} 的<unused98>标签部分替换失败，仍有剩余标签")
                else:
                    stats['unused98_replaced'] += 1
            else:
                # response字段存在但无法提取代码，记录为未替换
                stats['unused98_not_replaced'] += 1
                stats['unused98_not_replaced_ids'].append(record.get('id', 'unknown'))
                replacement_failed = True
                print(f"警告：记录ID {record.get('id', 'unknown')} 的response字段无法提取代码，<unused98>标签未替换")
        else:
            # 没有response字段，记录为未替换
            stats['unused98_not_replaced'] += 1
            stats['unused98_not_replaced_ids'].append(record.get('id', 'unknown'))
            replacement_failed = True
            print(f"警告：记录ID {record.get('id', 'unknown')} 缺少response字段，<unused98>标签未替换")
    
    # 如果替换失败，跳过这条记录
    if replacement_failed:
        return False, stats
    
    return True, stats


def process_jsonl_file(input_file: str, output_dir: str, data_type: str) -> dict:
    """
    处理单个JSONL文件，使用指定的数据类型
    
    Args:
        input_file: 输入JSONL文件路径
        output_dir: 输出目录路径
        data_type: 数据类型 ('fields' 或 'prompt')
        
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
                
                record = safe_json_loads(line, line_num)
                if record:  # 只添加成功解析的记录
                    data.append(record)
                else:
                    print(f"跳过第 {line_num} 行（解析失败）")
        
        print(f"成功读取 {len(data)} 条有效记录")
        
        if len(data) == 0:
            print("没有成功解析任何记录，请检查文件格式")
            return {
                'total': 0,
                'fields_processed': 0,
                'prompt_processed': 0,
                'skipped': 0,
                'unknown_type': 0
            }
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {input_file}")
        return {'total': 0, 'fields_processed': 0, 'prompt_processed': 0, 'skipped': 0, 'unknown_type': 0}
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return {'total': 0, 'fields_processed': 0, 'prompt_processed': 0, 'skipped': 0, 'unknown_type': 0}
    
    # 处理每条记录
    stats = {
        'total': len(data),
        'fields_processed': 0,
        'prompt_processed': 0,
        'skipped': 0,
        'unknown_type': 0,
        'fields_missing_fields': 0,
        'unused98_replaced': 0,
        'id_generated': 0,
        'fields_renamed': 0,
        'external_imported_extracted': 0,
        'unused98_not_replaced': 0,
        'unused98_not_replaced_ids': []
    }
    
    for i, record in enumerate(data):
        # 根据指定的数据类型处理记录
        if data_type == 'fields':
            success, record_stats = process_fields_record(record, i)
            if success:
                stats['fields_processed'] += 1
            stats['fields_missing_fields'] += record_stats.get('missing_fields', 0)
            stats['id_generated'] += record_stats.get('id_generated', 0)
            stats['fields_renamed'] += record_stats.get('fields_renamed', 0)
            
        elif data_type == 'prompt':
            success, record_stats = process_prompt_record(record, i)
            if success:
                stats['prompt_processed'] += 1
            stats['unused98_replaced'] += record_stats.get('unused98_replaced', 0)
            stats['id_generated'] += record_stats.get('id_generated', 0)
            stats['fields_renamed'] += record_stats.get('fields_renamed', 0)
            stats['external_imported_extracted'] += record_stats.get('external_imported_extracted', 0)
            stats['unused98_not_replaced'] += record_stats.get('unused98_not_replaced', 0)
            stats['unused98_not_replaced_ids'].extend(record_stats.get('unused98_not_replaced_ids', []))
            
        else:
            record['text'] = ""
            stats['unknown_type'] += 1
            stats['skipped'] += 1
        
        if (i + 1) % 1000 == 0:
            print(f"已处理 {i + 1}/{len(data)} 条记录")
    
    # 生成输出文件名
    input_path = Path(input_file)
    base_name = input_path.stem
    
    # 保存处理后的数据（只保存成功处理的记录）
    output_file = Path(output_dir) / f"{base_name}_with_text.jsonl"
    try:
        saved_count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in data:
                # 检查记录是否成功处理（有text字段且不为空，或者没有<unused98>标签）
                if data_type == 'prompt':
                    # prompt格式：需要有text字段，且如果原本有<unused98>标签则必须成功替换
                    if 'text' in record and record['text']:
                        # 如果text中仍有<unused98>标签，说明替换失败，跳过
                        if '<unused98>' not in record['text']:
                            json.dump(record, f, ensure_ascii=False)
                            f.write('\n')
                            saved_count += 1
                elif data_type == 'fields':
                    # fields格式：有text字段即可
                    if 'text' in record:
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n')
                        saved_count += 1
                else:
                    # 其他类型，直接保存
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
                    saved_count += 1
        
        print(f"✅ 处理后的数据已保存到: {output_file}")
        print(f"✅ 实际保存记录数: {saved_count}/{len(data)}")
        if saved_count < len(data):
            print(f"⚠️  过滤掉了 {len(data) - saved_count} 条替换失败的记录")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")
        return stats
    
    # 输出统计信息
    print(f"\n🎯 处理完成！")
    print(f"总记录数: {stats['total']}")
    print(f"Fields格式处理: {stats['fields_processed']}")
    print(f"Prompt格式处理: {stats['prompt_processed']}")
    print(f"跳过记录: {stats['skipped']}")
    print(f"未知类型: {stats['unknown_type']}")
    print(f"缺少字段: {stats['fields_missing_fields']}")
    print(f"替换标签: {stats['unused98_replaced']}")
    print(f"生成ID: {stats['id_generated']}")
    print(f"字段重命名: {stats['fields_renamed']}")
    print(f"提取external_imported: {stats['external_imported_extracted']}")
    print(f"标签替换失败: {stats['unused98_not_replaced']}")
    
    # 输出替换失败的记录ID
    if stats['unused98_not_replaced'] > 0:
        print(f"标签替换失败的记录ID: {stats['unused98_not_replaced_ids']}")
    
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


def batch_process_directory(input_dir: str, output_dir: str, data_type: str) -> dict:
    """
    批量处理指定目录下的所有JSONL文件
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        data_type: 数据类型 ('fields' 或 'prompt')
        
    Returns:
        总体统计信息
    """
    print(f"🚀 开始批量处理目录: {input_dir}")
    
    # 获取所有JSONL文件
    jsonl_files = get_jsonl_files(input_dir)
    
    if not jsonl_files:
        print(f"❌ 在 {input_dir} 中没有找到任何JSONL文件")
        return {
            'total_files': 0,
            'total_records': 0,
            'total_fields_processed': 0,
            'total_prompt_processed': 0,
            'total_skipped': 0
        }
    
    # 批量处理
    total_stats = {
        'total_files': len(jsonl_files),
        'total_records': 0,
        'total_fields_processed': 0,
        'total_prompt_processed': 0,
        'total_skipped': 0,
        'total_unknown_type': 0,
        'total_fields_missing_fields': 0,
        'total_unused98_replaced': 0,
        'total_id_generated': 0,
        'total_fields_renamed': 0,
        'total_external_imported_extracted': 0,
        'total_unused98_not_replaced': 0,
        'total_unused98_not_replaced_ids': []
    }
    
    for i, input_file in enumerate(jsonl_files, 1):
        print(f"\n📁 处理文件 {i}/{len(jsonl_files)}: {os.path.basename(input_file)}")
        
        # 处理文件
        stats = process_jsonl_file(input_file, output_dir, data_type)
        
        # 累计统计信息
        total_stats['total_records'] += stats['total']
        total_stats['total_fields_processed'] += stats['fields_processed']
        total_stats['total_prompt_processed'] += stats['prompt_processed']
        total_stats['total_skipped'] += stats['skipped']
        total_stats['total_unknown_type'] += stats['unknown_type']
        total_stats['total_fields_missing_fields'] += stats.get('fields_missing_fields', 0)
        total_stats['total_unused98_replaced'] += stats.get('unused98_replaced', 0)
        total_stats['total_id_generated'] += stats.get('id_generated', 0)
        total_stats['total_fields_renamed'] += stats.get('fields_renamed', 0)
        total_stats['total_external_imported_extracted'] += stats.get('external_imported_extracted', 0)
        total_stats['total_unused98_not_replaced'] += stats.get('unused98_not_replaced', 0)
        total_stats['total_unused98_not_replaced_ids'].extend(stats.get('unused98_not_replaced_ids', []))
        
        print(f"✅ 文件处理完成: {os.path.basename(input_file)}")
    
    return total_stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='统一文本拼接处理器 - 支持Fields和Prompt两种数据格式')
    
    # 基本参数
    parser.add_argument('--output-dir', default='trans_text_data', 
                       help='输出目录路径（默认: trans_text_data）')
    parser.add_argument('--single-file', help='处理单个文件（可选）')
    
    # 处理模式参数
    parser.add_argument('--fields-only', action='store_true', 
                       help='只处理Fields格式数据（默认从bg_data_select读取）')
    parser.add_argument('--prompt-only', action='store_true', 
                       help='只处理Prompt格式数据（默认从bg_data读取）')
    parser.add_argument('--both', action='store_true', 
                       help='处理两种格式数据（默认行为）')
    
    # 自定义输入目录
    parser.add_argument('--fields-dir', default='bg_data_select',
                       help='Fields格式数据输入目录（默认: bg_data_select）')
    parser.add_argument('--prompt-dir', default='bg_data',
                       help='Prompt格式数据输入目录（默认: bg_data）')
    
    # 强制指定数据类型
    parser.add_argument('--force-type', choices=['fields', 'prompt'],
                       help='强制指定数据类型，跳过自动检测')
    
    args = parser.parse_args()
    
    # 获取当前脚本所在目录
    curdir = os.path.dirname(__file__)
    
    # 处理输出目录
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = Path(curdir) / output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🎯 统一文本拼接处理器启动")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 处理单个文件
    if args.single_file:
        if not Path(args.single_file).exists():
            print(f"❌ 文件不存在: {args.single_file}")
            return
        
        print(f"处理单个文件: {args.single_file}")
        # 对于单个文件，如果没有强制指定类型，则需要检测
        if args.force_type:
            file_data_type = args.force_type
        else:
            # 简单检测：读取第一条记录判断类型
            try:
                with open(args.single_file, 'r', encoding='utf-8') as f:
                    line = f.readline().strip()
                    if line:
                        record = json.loads(line)
                        file_data_type = detect_data_type(record)
                    else:
                        print("警告：文件为空，默认使用fields类型")
                        file_data_type = 'fields'
            except Exception as e:
                print(f"检测文件类型失败: {e}，默认使用fields类型")
                file_data_type = 'fields'
        
        stats = process_jsonl_file(args.single_file, str(output_dir), file_data_type)
        return
    
    # 确定处理模式
    process_fields = args.fields_only or args.both or (not args.prompt_only and not args.fields_only)
    process_prompt = args.prompt_only or args.both or (not args.prompt_only and not args.fields_only)
    
    overall_stats = {
        'total_files': 0,
        'total_records': 0,
        'total_fields_processed': 0,
        'total_prompt_processed': 0,
        'total_skipped': 0
    }
    
    # 处理Fields格式数据
    if process_fields:
        fields_dir = Path(args.fields_dir)
        if not fields_dir.is_absolute():
            fields_dir = Path(curdir) / fields_dir
        
        if fields_dir.exists():
            print(f"\n🔧 处理Fields格式数据 (来源: {fields_dir})")
            fields_stats = batch_process_directory(str(fields_dir), str(output_dir), 'fields')
            
            # 累计统计
            overall_stats['total_files'] += fields_stats['total_files']
            overall_stats['total_records'] += fields_stats['total_records']
            overall_stats['total_fields_processed'] += fields_stats['total_fields_processed']
            overall_stats['total_skipped'] += fields_stats['total_skipped']
        else:
            print(f"⚠️  Fields格式输入目录不存在: {fields_dir}")
    
    # 处理Prompt格式数据
    if process_prompt:
        prompt_dir = Path(args.prompt_dir)
        if not prompt_dir.is_absolute():
            prompt_dir = Path(curdir) / prompt_dir
        
        if prompt_dir.exists():
            print(f"\n🔧 处理Prompt格式数据 (来源: {prompt_dir})")
            prompt_stats = batch_process_directory(str(prompt_dir), str(output_dir), 'prompt')
            
            # 累计统计
            overall_stats['total_files'] += prompt_stats['total_files']
            overall_stats['total_records'] += prompt_stats['total_records']
            overall_stats['total_prompt_processed'] += prompt_stats['total_prompt_processed']
            overall_stats['total_skipped'] += prompt_stats['total_skipped']
        else:
            print(f"⚠️  Prompt格式输入目录不存在: {prompt_dir}")
    
    # 输出总体统计信息
    print("\n" + "=" * 60)
    print("🎯 所有处理完成！")
    print(f"总文件数: {overall_stats['total_files']}")
    print(f"总记录数: {overall_stats['total_records']}")
    print(f"Fields格式处理: {overall_stats['total_fields_processed']}")
    print(f"Prompt格式处理: {overall_stats['total_prompt_processed']}")
    print(f"总跳过数: {overall_stats['total_skipped']}")
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()
