#!/usr/bin/env python3
"""
从JSONL文件的prompt字段中提取三段内容并拼接成新的text字段
同时将<unused98>标签替换成response字段中```arkts\n和\n```之间的内容
批量处理bg_data文件夹下的所有JSONL文件
为每条记录生成基于path的稳定ID，并标准化字段名
"""

import json
import re
import os
import hashlib
from pathlib import Path
from typing import List


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
                print(f"警告：无法找到 {part_name} 部分")
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
            print("警告：无法在response中找到```arkts\n...\n```格式的代码")
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
        print("警告：response_code为空，无法替换<unused98>标签")
        return text
    
    try:
        # 替换所有<unused98>标签
        replaced_text = text.replace('<unused98>', response_code)
        
        # 统计替换次数
        original_count = text.count('<unused98>')
        if original_count > 0:
            print(f"成功替换 {original_count} 个<unused98>标签")
        
        return replaced_text
        
    except Exception as e:
        print(f"替换<unused98>标签时发生错误: {e}")
        return text


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


def generate_stable_id(relative_path: str) -> str:
    """
    基于relativePath生成稳定的ID
    
    Args:
        relative_path: 相对路径字符串
        
    Returns:
        64位十六进制SHA256哈希ID
    """
    if not relative_path or not isinstance(relative_path, str):
        # 如果没有relativePath，生成一个随机ID
        import uuid
        return str(uuid.uuid4())
    
    try:
        # 使用SHA256哈希生成稳定ID
        stable_id = hashlib.sha256(relative_path.encode('utf-8')).hexdigest()
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

def process_jsonl_file(input_file: str, output_file: str) -> dict:
    """
    处理单个JSONL文件，为每条记录添加text字段，并替换<unused98>标签
    同时为每条记录生成基于path的稳定ID，并标准化字段名
    
    Args:
        input_file: 输入JSONL文件路径
        output_file: 输出JSONL文件路径
        
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
                'total_records': 0,
                'processed_count': 0,
                'skipped_count': 0,
                'unused98_replaced_count': 0,
                'id_generated_count': 0,
                'fields_renamed': 0
            }
            
    except FileNotFoundError:
        print(f"文件不存在: {input_file}")
        return {
            'total_records': 0,
            'processed_count': 0,
            'skipped_count': 0,
            'unused98_replaced_count': 0,
            'id_generated_count': 0,
            'fields_renamed': 0
        }
    except Exception as e:
        print(f"读取文件失败: {e}")
        return {
            'total_records': 0,
            'processed_count': 0,
            'skipped_count': 0,
            'unused98_replaced_count': 0,
            'id_generated_count': 0,
            'fields_renamed': 0
        }
    
    # 处理每条记录
    processed_count = 0
    skipped_count = 0
    unused98_replaced_count = 0
    id_generated_count = 0
    fields_renamed_count = 0
    
    for i, record in enumerate(data):
        if 'prompt' not in record:
            print(f"警告：第 {i+1} 条记录缺少 'prompt' 字段")
            record['text'] = ""
            skipped_count += 1
            continue
        
        # 字段名标准化和字段值处理
        # 1. 处理projectName字段
        if 'projectName' in record:
            # 如果存在projectName，重命名为project_name
            record['project_name'] = record.pop('projectName')
            fields_renamed_count += 1
            print(f"第 {i+1} 条记录：字段名 'projectName' 已改为 'project_name'")
        elif 'project_name' not in record:
            # 如果既没有projectName也没有project_name，从repoUrl提取
            repo_url = record.get('repoUrl', '')
            if repo_url:
                project_name, _ = extract_project_info_from_repo_url(repo_url)
                if project_name:
                    record['project_name'] = project_name
                    print(f"第 {i+1} 条记录：从repoUrl提取project_name: '{project_name}'")
        
        # 2. 处理relativePath字段
        if 'relativePath' in record:
            # 如果存在relativePath，重命名为path
            record['path'] = record.pop('relativePath')
            fields_renamed_count += 1
            print(f"第 {i+1} 条记录：字段名 'relativePath' 已改为 'path'")
        elif 'path' not in record:
            # 如果既没有relativePath也没有path，从repoUrl提取
            repo_url = record.get('repoUrl', '')
            if repo_url:
                _, path = extract_project_info_from_repo_url(repo_url)
                if path:
                    record['path'] = path
                    print(f"第 {i+1} 条记录：从repoUrl提取path: '{path}'")
        
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
        
        # 提取text内容
        text_content = extract_text_from_prompt(record['prompt'])
        record['text'] = text_content
        processed_count += 1
        
        # 处理<unused98>标签替换
        if 'response' in record and '<unused98>' in text_content:
            response_code = extract_response_code(record['response'])
            if response_code:
                record['text'] = replace_unused98_tags(text_content, response_code)
                unused98_replaced_count += 1
                print(f"第 {i+1} 条记录：成功替换<unused98>标签")
        
        if (i + 1) % 100 == 0:
            print(f"已处理 {i + 1}/{len(data)} 条记录")
    
    # 保存处理后的数据
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in data:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        print(f"成功保存到: {output_file}")
    except Exception as e:
        print(f"保存文件失败: {e}")
        return {
            'total_records': len(data),
            'processed_count': 0,
            'skipped_count': 0,
            'unused98_replaced_count': 0,
            'id_generated_count': 0
        }
    
    # 返回统计信息
    return {
        'total_records': len(data),
        'processed_count': processed_count,
        'skipped_count': skipped_count,
        'unused98_replaced_count': unused98_replaced_count,
        'id_generated_count': id_generated_count,
        'fields_renamed': fields_renamed_count
    }


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
    批量处理指定输入目录下的所有JSONL文件
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
    """
    print(f"🚀 开始批量处理文件...")
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
        'total_unused98_replaced': 0,
        'total_id_generated': 0,
        'total_fields_renamed': 0
    }
    
    for i, input_file in enumerate(jsonl_files, 1):
        print(f"\n📁 处理文件 {i}/{len(jsonl_files)}: {os.path.basename(input_file)}")
        
        # 生成输出文件路径
        input_path = Path(input_file)
        output_file = Path(output_dir) / f"{input_path.stem}_with_text{input_path.suffix}"
        
        # 处理文件
        stats = process_jsonl_file(input_file, str(output_file))
        
        # 累计统计信息
        total_stats['total_records'] += stats['total_records']
        total_stats['total_processed'] += stats['processed_count']
        total_stats['total_skipped'] += stats['skipped_count']
        total_stats['total_unused98_replaced'] += stats['unused98_replaced_count']
        total_stats['total_id_generated'] += stats['id_generated_count']
        total_stats['total_fields_renamed'] += stats['fields_renamed']
        
        print(f"✅ 文件处理完成: {os.path.basename(input_file)}")
        print(f"   记录数: {stats['total_records']}, 处理: {stats['processed_count']}, 跳过: {stats['skipped_count']}, 替换标签: {stats['unused98_replaced_count']}, 生成ID: {stats['id_generated_count']}, 字段重命名: {stats['fields_renamed']}")
    
    # 输出总体统计信息
    print("\n" + "=" * 60)
    print("🎯 批量处理完成！")
    print(f"总文件数: {total_stats['total_files']}")
    print(f"总记录数: {total_stats['total_records']}")
    print(f"总处理数: {total_stats['total_processed']}")
    print(f"总跳过数: {total_stats['total_skipped']}")
    print(f"总替换标签数: {total_stats['total_unused98_replaced']}")
    print(f"总生成ID数: {total_stats['total_id_generated']}")
    print(f"总字段重命名数: {total_stats['total_fields_renamed']}")
    print(f"输出目录: {output_dir}")


def check_file_format(input_file: str) -> bool:
    """
    检查文件格式是否正确
    
    Args:
        input_file: 输入文件路径
        
    Returns:
        格式是否正确
    """
    print(f"检查文件格式: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # 读取前几行进行检查
            for i, line in enumerate(f, 1):
                if i > 5:  # 只检查前5行
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        print(f"第 {i} 行：不是有效的JSON对象")
                        return False
                    print(f"第 {i} 行：格式正确，包含字段: {list(record.keys())}")
                except json.JSONDecodeError as e:
                    print(f"第 {i} 行：JSON格式错误 - {e}")
                    print(f"问题行内容: {line[:100]}...")
                    return False
                    
        print("文件格式检查完成")
        return True
        
    except Exception as e:
        print(f"检查文件时发生错误: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    parser = argparse.ArgumentParser(description='批量处理JSONL文件，提取text内容并替换<unused98>标签，同时生成基于path的稳定ID，并标准化字段名')
    parser.add_argument('--input-dir', default=str(current_dir / 'bg_data'), help='输入目录路径（默认: 与脚本同级目录下的bg_data）')
    parser.add_argument('--output-dir', default=str(current_dir / 'trans_text_data'), help='输出目录路径（默认: 与脚本同级目录下的trans_text_data）')
    parser.add_argument('--single-file', help='处理单个文件（可选）')
    parser.add_argument('--check', action='store_true', help='只检查文件格式，不进行处理')
    
    args = parser.parse_args()
    
    # 如果指定了单个文件
    if args.single_file:
        if not Path(args.single_file).exists():
            print(f"❌ 文件不存在: {args.single_file}")
            return
        
        # 生成输出文件路径
        input_path = Path(args.single_file)
        output_file = Path(args.output_dir) / f"{input_path.stem}_with_text{input_path.suffix}"
        
        # 先检查文件格式
        if not check_file_format(args.single_file):
            print("文件格式有问题，请修复后再试")
            return
        
        # 处理单个文件
        stats = process_jsonl_file(args.single_file, str(output_file))
        print(f"\n处理完成！")
        print(f"记录数: {stats['total_records']}")
        print(f"处理数: {stats['processed_count']}")
        print(f"跳过数: {stats['skipped_count']}")
        print(f"替换标签数: {stats['unused98_replaced_count']}")
        print(f"生成ID数: {stats['id_generated_count']}")
        print(f"字段重命名数: {stats['fields_renamed']}")
        
    else:
        # 批量处理
        input_dir = args.input_dir
        output_dir = args.output_dir
        
        if not Path(input_dir).exists():
            print(f"❌ 输入目录不存在: {input_dir}")
            return
        
        # 批量处理文件
        batch_process_files(input_dir, output_dir)


if __name__ == "__main__":
    main() 