#!/usr/bin/env python3
"""
统一的文本处理脚本
支持两种数据格式的拼接，最终输出到统一目录：
1. 从prompt字段提取三段内容拼接（extract_prompt_text功能）
2. 拼接above_functions + source_method_code + below_functions（concatenate_fields功能）
"""

import json
import re
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse


class UnifiedTextProcessor:
    """统一文本处理器"""
    
    def __init__(self, output_dir: str = "unified_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 统计信息
        self.stats = {
            'prompt_type': {
                'total': 0, 'processed': 0, 'skipped': 0, 
                'unused98_replaced': 0, 'external_imported': 0
            },
            'fields_type': {
                'total': 0, 'processed': 0, 'skipped': 0, 'missing_fields': 0
            },
            'id_generated': 0,
            'fields_renamed': 0
        }
    
    def detect_data_type(self, record: Dict) -> str:
        """
        检测数据类型
        
        Args:
            record: JSONL记录
            
        Returns:
            'prompt' 或 'fields' 或 'unknown'
        """
        if 'prompt' in record:
            return 'prompt'
        elif all(field in record for field in ['above_functions', 'source_method_code', 'below_functions']):
            return 'fields'
        else:
            return 'unknown'
    
    def extract_text_from_prompt(self, prompt: str) -> str:
        """
        从prompt中提取三段内容并拼接，保留原有空格格式
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
                    extracted_parts[part_name] = match.group(1)
                else:
                    extracted_parts[part_name] = ""
            
            # 拼接三段内容，保持原有格式
            combined_text = (
                extracted_parts.get('first', '') + '\n\n' + 
                extracted_parts.get('second', '') + '\n\n' + 
                extracted_parts.get('third', '')
            )
            
            return combined_text.rstrip('\n')
            
        except Exception as e:
            print(f"提取prompt内容时发生错误: {e}")
            return ""
    
    def extract_response_code(self, response: str) -> str:
        """从response字段中提取```arkts\n和\n```之间的代码内容"""
        if not response or not isinstance(response, str):
            return ""
        
        try:
            pattern = r'```arkts\n(.*?)\n```'
            match = re.search(pattern, response, re.DOTALL)
            return match.group(1) if match else ""
        except Exception as e:
            print(f"提取response代码时发生错误: {e}")
            return ""
    
    def replace_unused98_tags(self, text: str, response_code: str) -> str:
        """将文本中的<unused98>标签替换成response代码"""
        if not text or not isinstance(text, str) or not response_code:
            return text
        
        try:
            replaced_text = text.replace('<unused98>', response_code)
            original_count = text.count('<unused98>')
            if original_count > 0:
                self.stats['prompt_type']['unused98_replaced'] += original_count
            return replaced_text
        except Exception as e:
            print(f"替换<unused98>标签时发生错误: {e}")
            return text
    
    def extract_external_imported(self, prompt: str) -> str:
        """提取external_imported信息"""
        if not prompt or not isinstance(prompt, str):
            return ""
        
        try:
            pattern = r'Below are some information from external classes imported by current file:\n```arkts\n(.*?)```'
            match = re.search(pattern, prompt, re.DOTALL)
            if match:
                self.stats['prompt_type']['external_imported'] += 1
                return match.group(1)
            return ""
        except Exception as e:
            print(f"提取external_imported时发生错误: {e}")
            return ""
    
    def concatenate_fields(self, record: Dict) -> str:
        """拼接三个字段：above_functions + source_method_code + below_functions"""
        
        def process_field_value(value):
            if value is None:
                return ''
            elif isinstance(value, str):
                return value
            elif isinstance(value, (list, tuple)):
                if len(value) == 0:
                    return ''
                elif all(isinstance(item, str) for item in value):
                    return '\n'.join(item for item in value if item)
                else:
                    return str(value)
            elif isinstance(value, dict):
                try:
                    json_str = json.dumps(value, ensure_ascii=False)
                    return json_str[1:-1] if json_str.startswith('{') and json_str.endswith('}') else json_str
                except:
                    return str(value)
            else:
                return str(value)
        
        # 获取三个字段的值
        above_functions = process_field_value(record.get('above_functions', ''))
        source_method_code = process_field_value(record.get('source_method_code', ''))
        below_functions = process_field_value(record.get('below_functions', ''))
        
        # 直接拼接三个字段
        return above_functions + source_method_code + below_functions
    
    def generate_stable_id(self, path: str) -> str:
        """基于path生成稳定的ID"""
        if not path or not isinstance(path, str):
            import uuid
            return str(uuid.uuid4())
        
        try:
            return hashlib.sha256(path.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"生成ID时发生错误: {e}")
            import uuid
            return str(uuid.uuid4())
    
    def extract_project_info_from_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """从repoUrl中提取project_name和path信息"""
        if not repo_url or not isinstance(repo_url, str):
            return "", ""
        
        try:
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            parts = repo_url.split('/')
            if len(parts) >= 1:
                repo_name = parts[-1]
                return repo_name, repo_name
            else:
                return "", ""
        except Exception as e:
            print(f"解析repoUrl时发生错误: {e}")
            return "", ""
    
    def standardize_fields(self, record: Dict, record_index: int) -> Dict:
        """标准化字段名"""
        # 处理projectName字段
        if 'projectName' in record:
            record['project_name'] = record.pop('projectName')
            self.stats['fields_renamed'] += 1
            print(f"第 {record_index+1} 条记录：字段名 'projectName' 已改为 'project_name'")
        elif 'project_name' not in record:
            repo_url = record.get('repoUrl', '')
            if repo_url:
                project_name, _ = self.extract_project_info_from_repo_url(repo_url)
                if project_name:
                    record['project_name'] = project_name
                    print(f"第 {record_index+1} 条记录：从repoUrl提取project_name: '{project_name}'")
        
        # 处理relativePath和filePath字段
        if 'relativePath' in record:
            record['path'] = record.pop('relativePath')
            self.stats['fields_renamed'] += 1
            print(f"第 {record_index+1} 条记录：字段名 'relativePath' 已改为 'path'")
        elif 'filePath' in record:
            record['path'] = record.pop('filePath')
            self.stats['fields_renamed'] += 1
            print(f"第 {record_index+1} 条记录：字段名 'filePath' 已改为 'path'")
        elif 'path' not in record:
            repo_url = record.get('repoUrl', '')
            if repo_url:
                _, path = self.extract_project_info_from_repo_url(repo_url)
                if path:
                    record['path'] = path
                    print(f"第 {record_index+1} 条记录：从repoUrl提取path: '{path}'")
        
        return record
    
    def process_prompt_type(self, record: Dict, record_index: int) -> Dict:
        """处理prompt类型的数据"""
        self.stats['prompt_type']['total'] += 1
        
        if 'prompt' not in record:
            print(f"警告：第 {record_index+1} 条记录缺少 'prompt' 字段")
            record['text'] = ""
            self.stats['prompt_type']['skipped'] += 1
            return record
        
        # 提取text内容
        text_content = self.extract_text_from_prompt(record['prompt'])
        record['text'] = text_content
        
        # 提取external_imported
        external_imported = self.extract_external_imported(record['prompt'])
        if external_imported:
            record['external_imported'] = external_imported
        
        # 处理<unused98>标签替换
        if 'response' in record and '<unused98>' in text_content:
            response_code = self.extract_response_code(record['response'])
            if response_code:
                record['text'] = self.replace_unused98_tags(text_content, response_code)
                print(f"第 {record_index+1} 条记录：成功替换<unused98>标签")
        
        self.stats['prompt_type']['processed'] += 1
        return record
    
    def process_fields_type(self, record: Dict, record_index: int) -> Dict:
        """处理fields类型的数据"""
        self.stats['fields_type']['total'] += 1
        
        # 检查是否包含所需的字段
        required_fields = ['above_functions', 'source_method_code', 'below_functions']
        missing_fields = [field for field in required_fields if field not in record]
        
        if missing_fields:
            print(f"警告：第 {record_index+1} 条记录缺少字段: {missing_fields}")
            record['text'] = ""
            record['concatenation_status'] = f"缺少字段: {', '.join(missing_fields)}"
            self.stats['fields_type']['missing_fields'] += 1
            return record
        
        # 拼接字段
        try:
            concatenated_text = self.concatenate_fields(record)
            record['text'] = concatenated_text
            record['concatenation_status'] = "成功拼接"
            self.stats['fields_type']['processed'] += 1
        except Exception as e:
            print(f"警告：第 {record_index+1} 条记录拼接失败: {e}")
            record['text'] = ""
            record['concatenation_status'] = f"拼接失败: {str(e)}"
            self.stats['fields_type']['skipped'] += 1
        
        return record
    
    def process_file(self, input_file: str, file_type: str = 'auto') -> bool:
        """
        处理单个文件
        
        Args:
            input_file: 输入文件路径
            file_type: 文件类型 ('prompt', 'fields', 'auto')
            
        Returns:
            是否处理成功
        """
        print(f"开始处理文件: {input_file}")
        
        # 读取数据
        try:
            data = []
            with open(input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        data.append(record)
                    except json.JSONDecodeError as e:
                        print(f"第 {line_num} 行JSON解析失败: {e}")
                        continue
            
            print(f"成功读取 {len(data)} 条记录")
            
            if len(data) == 0:
                print("没有成功解析任何记录")
                return False
                
        except Exception as e:
            print(f"读取文件失败: {e}")
            return False
        
        # 处理每条记录
        for i, record in enumerate(data):
            # 标准化字段名
            record = self.standardize_fields(record, i)
            
            # 生成ID
            file_path = record.get('path', '')
            if file_path:
                record['id'] = self.generate_stable_id(file_path)
                self.stats['id_generated'] += 1
                print(f"第 {i+1} 条记录：基于路径 '{file_path}' 生成ID: {record['id'][:8]}...")
            else:
                record['id'] = self.generate_stable_id("")
                self.stats['id_generated'] += 1
            
            # 根据文件类型或自动检测进行处理
            if file_type == 'auto':
                data_type = self.detect_data_type(record)
            else:
                data_type = file_type
            
            if data_type == 'prompt':
                record = self.process_prompt_type(record, i)
            elif data_type == 'fields':
                record = self.process_fields_type(record, i)
            else:
                print(f"警告：第 {i+1} 条记录无法识别数据类型，跳过处理")
                record['text'] = ""
                record['processing_status'] = "未知数据类型"
            
            if (i + 1) % 100 == 0:
                print(f"已处理 {i + 1}/{len(data)} 条记录")
        
        # 保存处理后的数据
        input_path = Path(input_file)
        output_file = self.output_dir / f"{input_path.stem}_processed.jsonl"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for record in data:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            print(f"✅ 处理后的数据已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            return False
    
    def process_directory(self, input_dir: str, file_type: str = 'auto') -> None:
        """
        处理目录下的所有JSONL文件
        
        Args:
            input_dir: 输入目录路径
            file_type: 文件类型 ('prompt', 'fields', 'auto')
        """
        print(f"🚀 开始批量处理目录: {input_dir}")
        print(f"输出目录: {self.output_dir}")
        print("=" * 60)
        
        # 获取所有JSONL文件
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ 输入目录不存在: {input_dir}")
            return
        
        jsonl_files = []
        for ext in ['*.jsonl', '*.json']:
            jsonl_files.extend(list(input_path.glob(ext)))
        
        if not jsonl_files:
            print("❌ 没有找到任何JSONL文件")
            return
        
        print(f"找到 {len(jsonl_files)} 个文件")
        
        # 批量处理
        successful_files = 0
        for i, file_path in enumerate(jsonl_files, 1):
            print(f"\n📁 处理文件 {i}/{len(jsonl_files)}: {file_path.name}")
            
            if self.process_file(str(file_path), file_type):
                successful_files += 1
        
        # 输出统计信息
        self.print_stats()
        print(f"\n🎯 批量处理完成！成功处理 {successful_files}/{len(jsonl_files)} 个文件")
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("📊 处理统计信息")
        print("=" * 60)
        
        print(f"📝 Prompt类型数据:")
        print(f"   总记录数: {self.stats['prompt_type']['total']}")
        print(f"   成功处理: {self.stats['prompt_type']['processed']}")
        print(f"   跳过记录: {self.stats['prompt_type']['skipped']}")
        print(f"   替换标签: {self.stats['prompt_type']['unused98_replaced']}")
        print(f"   提取外部: {self.stats['prompt_type']['external_imported']}")
        
        print(f"\n🔗 Fields类型数据:")
        print(f"   总记录数: {self.stats['fields_type']['total']}")
        print(f"   成功处理: {self.stats['fields_type']['processed']}")
        print(f"   跳过记录: {self.stats['fields_type']['skipped']}")
        print(f"   缺少字段: {self.stats['fields_type']['missing_fields']}")
        
        print(f"\n🆔 通用处理:")
        print(f"   生成ID数: {self.stats['id_generated']}")
        print(f"   字段重命名: {self.stats['fields_renamed']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='统一的文本处理脚本，支持prompt和fields两种数据格式的拼接'
    )
    parser.add_argument('--prompt-dir', help='包含prompt格式数据的目录路径')
    parser.add_argument('--fields-dir', help='包含fields格式数据的目录路径')
    parser.add_argument('--single-file', help='处理单个文件（自动检测类型）')
    parser.add_argument('--output-dir', default='unified_output', help='统一输出目录路径（默认: unified_output）')
    parser.add_argument('--file-type', choices=['prompt', 'fields', 'auto'], default='auto', 
                       help='强制指定文件类型（默认: auto自动检测）')
    
    args = parser.parse_args()
    
    if not any([args.prompt_dir, args.fields_dir, args.single_file]):
        print("❌ 请至少指定一个输入源: --prompt-dir, --fields-dir, 或 --single-file")
        return
    
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 初始化处理器
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = current_dir / output_dir
    
    processor = UnifiedTextProcessor(str(output_dir))
    
    # 处理单个文件
    if args.single_file:
        file_path = Path(args.single_file)
        if not file_path.is_absolute():
            file_path = current_dir / file_path
        
        if file_path.exists():
            processor.process_file(str(file_path), args.file_type)
        else:
            print(f"❌ 文件不存在: {file_path}")
        return
    
    # 处理prompt格式数据目录
    if args.prompt_dir:
        prompt_dir = Path(args.prompt_dir)
        if not prompt_dir.is_absolute():
            prompt_dir = current_dir / prompt_dir
        
        print(f"🔍 处理prompt格式数据...")
        processor.process_directory(str(prompt_dir), 'prompt')
    
    # 处理fields格式数据目录
    if args.fields_dir:
        fields_dir = Path(args.fields_dir)
        if not fields_dir.is_absolute():
            fields_dir = current_dir / fields_dir
        
        print(f"\n🔗 处理fields格式数据...")
        processor.process_directory(str(fields_dir), 'fields')
    
    print(f"\n🎯 所有处理完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()
