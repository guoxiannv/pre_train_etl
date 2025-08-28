#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析train文件夹中的编程语言分布
从每个文件的<events>部分提取被编辑的文件路径，并根据文件后缀名确定编程语言
"""

import os
import re
from collections import Counter
from pathlib import Path
import json

# 定义文件后缀名到编程语言的映射
LANGUAGE_MAPPING = {
    # 常见编程语言
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'React JSX',
    '.tsx': 'React TSX',
    '.rb': 'Ruby',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.php': 'PHP',
    '.go': 'Go',
    '.rs': 'Rust',
    '.zig': 'Zig',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.r': 'R',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
    '.pl': 'Perl',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.fish': 'Fish',
    '.ps1': 'PowerShell',
    '.bat': 'Batch',
    '.cmd': 'Command',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.json': 'JSON',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
    '.md': 'Markdown',
    '.txt': 'Text',
    '.log': 'Log',
    '.lock': 'Lock',
    '.gitignore': 'Git',
    '.dockerfile': 'Docker',
    '.dockerignore': 'Docker',
    '.env': 'Environment',
    '.properties': 'Properties',
    '.gradle': 'Gradle',
    '.pom.xml': 'Maven',
    '.sbt': 'SBT',
    '.cabal': 'Cabal',
    '.cargo': 'Cargo',
    '.composer.json': 'Composer',
    '.package.json': 'NPM',
    '.requirements.txt': 'Python',
    '.setup.py': 'Python',
    '.pyproject.toml': 'Python',
    '.poetry.lock': 'Python',
    '.Pipfile': 'Python',
    '.Pipfile.lock': 'Python',
    '.gemfile': 'Ruby',
    '.gemfile.lock': 'Ruby',
    '.go.mod': 'Go',
    '.go.sum': 'Go',
    '.Cargo.toml': 'Rust',
    '.Cargo.lock': 'Rust',
    '.mix.exs': 'Elixir',
    '.mix.lock': 'Elixir',
    '.deps.edn': 'Clojure',
    '.project.clj': 'Clojure',
    '.build.sbt': 'Scala',
    '.build.sc': 'Scala',
    '.pom.xml': 'Maven',
    '.build.gradle': 'Gradle',
    '.build.gradle.kts': 'Gradle',
    '.settings.gradle': 'Gradle',
    '.settings.gradle.kts': 'Gradle',
    '.gradle.properties': 'Gradle',
    '.gradle-wrapper.properties': 'Gradle',
    '.gradle-wrapper.jar': 'Gradle',
    '.mvn': 'Maven',
    '.mvn/wrapper/maven-wrapper.properties': 'Maven',
    '.mvn/wrapper/maven-wrapper.jar': 'Maven',
    '.npmrc': 'NPM',
    '.yarnrc': 'Yarn',
    '.yarn.lock': 'Yarn',
    '.pnpm-lock.yaml': 'PNPM',
    '.bowerrc': 'Bower',
    '.bower.json': 'Bower',
    '.composer.json': 'Composer',
    '.composer.lock': 'Composer',
    '.nuget.config': 'NuGet',
    '.packages.config': 'NuGet',
    '.paket.dependencies': 'Paket',
    '.paket.lock': 'Paket',
    '.stack.yaml': 'Stack',
    '.stack.yaml.lock': 'Stack',
    '.cabal.project': 'Cabal',
    '.cabal.project.local': 'Cabal',
    '.cabal.project.local~': 'Cabal',
    '.cabal.project.local.bak': 'Cabal',
    '.cabal.project.local.old': 'Cabal',
    '.cabal.project.local.new': 'Cabal',
    '.cabal.project.local.tmp': 'Cabal',
    '.cabal.project.local.temp': 'Cabal',
    '.cabal.project.local.swp': 'Cabal',
    '.cabal.project.local.swo': 'Cabal',
    '.cabal.project.local.bak~': 'Cabal',
    '.cabal.project.local.old~': 'Cabal',
    '.cabal.project.local.new~': 'Cabal',
    '.cabal.project.local.tmp~': 'Cabal',
    '.cabal.project.local.temp~': 'Cabal',
    '.cabal.project.local.swp~': 'Cabal',
    '.cabal.project.local.swo~': 'Cabal',
    # 添加更多语言支持
    '.vue': 'Vue',
    '.dart': 'Dart',
    '.asm': 'Assembly',
    '.s': 'Assembly',
    '.graphql': 'GraphQL',
    '.gql': 'GraphQL',
    '.sol': 'Solidity',
    '.hs': 'Haskell',
    '.lhs': 'Haskell',
    '.elm': 'Elm',
    '.clj': 'Clojure',
    '.edn': 'Clojure',
    '.ex': 'Elixir',
    '.exs': 'Elixir',
    '.erl': 'Erlang',
    '.hrl': 'Erlang',
    '.fs': 'F#',
    '.fsx': 'F#',
    '.fsi': 'F#',
    '.ml': 'OCaml',
    '.mli': 'OCaml',
    '.re': 'Reason',
    '.rei': 'Reason',
    '.nim': 'Nim',
    '.cr': 'Crystal',
    '.jl': 'Julia',
    '.lua': 'Lua',
    '.tcl': 'Tcl',
    '.v': 'Verilog',
    '.sv': 'SystemVerilog',
    '.vhd': 'VHDL',
    '.vhdl': 'VHDL',
    '.coffee': 'CoffeeScript',
    '.litcoffee': 'CoffeeScript',
    '.iced': 'IcedCoffeeScript',
    '.ls': 'LiveScript',
    '.cljs': 'ClojureScript',
    '.cljc': 'ClojureScript',
    '.clj': 'ClojureScript',
    '.cljx': 'ClojureScript',
    '.cljs.edn': 'ClojureScript',
    '.boot': 'Boot',
    '.lein': 'Leiningen',
    '.project.clj': 'Leiningen',
    '.profiles.clj': 'Leiningen',
    '.user.clj': 'Leiningen',
    '.user.clj.bak': 'Leiningen',
    '.user.clj.old': 'Leiningen',
    '.user.clj.new': 'Leiningen',
    '.user.clj.tmp': 'Leiningen',
    '.user.clj.temp': 'Leiningen',
    '.user.clj.swp': 'Leiningen',
    '.user.clj.swo': 'Leiningen',
    '.user.clj.bak~': 'Leiningen',
    '.user.clj.old~': 'Leiningen',
    '.user.clj.new~': 'Leiningen',
    '.user.clj.tmp~': 'Leiningen',
    '.user.clj.temp~': 'Leiningen',
    '.user.clj.swp~': 'Leiningen',
    '.user.clj.swo~': 'Leiningen',
}

def get_language_from_filename(filename):
    """根据文件名确定编程语言"""
    # 获取文件扩展名
    file_path = Path(filename)
    
    # 检查完整文件名（包括点号开头的隐藏文件）
    if filename.startswith('.'):
        if filename in LANGUAGE_MAPPING:
            return LANGUAGE_MAPPING[filename]
    
    # 检查文件扩展名
    suffix = file_path.suffix.lower()
    if suffix in LANGUAGE_MAPPING:
        return LANGUAGE_MAPPING[suffix]
    
    # 检查多个扩展名的情况（如 .tar.gz）
    suffixes = ''.join(file_path.suffixes).lower()
    if suffixes in LANGUAGE_MAPPING:
        return LANGUAGE_MAPPING[suffixes]
    
    # 检查特定文件名模式
    filename_lower = filename.lower()
    for pattern, language in LANGUAGE_MAPPING.items():
        if pattern.lower() in filename_lower:
            return language
    
    return 'Unknown'

def extract_file_path_from_md(file_path):
    """从markdown文件中提取被编辑的文件路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配两种模式：
        # 1. "User edited "filename""
        # 2. "User edited file: "filename""
        pattern1 = r'User edited "([^"]+)"'
        pattern2 = r'User edited file: "([^"]+)"'
        
        # 先尝试第一种模式
        matches = re.findall(pattern1, content)
        if matches:
            return matches[0]  # 返回第一个匹配的文件路径
        
        # 再尝试第二种模式
        matches = re.findall(pattern2, content)
        if matches:
            return matches[0]  # 返回第一个匹配的文件路径
        
        return None
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def extract_labels_from_md(file_path):
    """从markdown文件中提取标签"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配 <labels> 标签内容
        pattern = r'<labels>\s*([^<]+)\s*</labels>'
        matches = re.findall(pattern, content)
        
        if matches:
            # 提取标签内容，按逗号分割并清理空白
            labels_text = matches[0].strip()
            labels = [label.strip() for label in labels_text.split(',') if label.strip()]
            return labels
        
        return []
        
    except Exception as e:
        print(f"Error reading labels from file {file_path}: {e}")
        return []

def analyze_language_and_labels_distribution(train_dir):
    """分析train文件夹中的语言分布和标签分布"""
    if not os.path.exists(train_dir):
        print(f"目录不存在: {train_dir}")
        return
    
    language_counter = Counter()
    labels_counter = Counter()
    file_language_map = {}
    file_labels_map = {}
    unknown_files = []
    files_without_labels = []
    
    # 遍历所有.md文件
    md_files = [f for f in os.listdir(train_dir) if f.endswith('.md')]
    total_files = len(md_files)
    
    print(f"开始分析 {total_files} 个文件...")
    
    for i, filename in enumerate(md_files, 1):
        if i % 100 == 0:
            print(f"已处理 {i}/{total_files} 个文件...")
        
        file_path = os.path.join(train_dir, filename)
        
        # 提取文件路径和语言
        edited_file = extract_file_path_from_md(file_path)
        if edited_file:
            language = get_language_from_filename(edited_file)
            language_counter[language] += 1
            file_language_map[filename] = {
                'edited_file': edited_file,
                'language': language
            }
            
            if language == 'Unknown':
                unknown_files.append((filename, edited_file))
        else:
            language_counter['No_File_Path'] += 1
            file_language_map[filename] = {
                'edited_file': None,
                'language': 'No_File_Path'
            }
        
        # 提取标签
        labels = extract_labels_from_md(file_path)
        if labels:
            # 统计每个标签
            for label in labels:
                labels_counter[label] += 1
            
            file_labels_map[filename] = labels
        else:
            files_without_labels.append(filename)
    
    return language_counter, labels_counter, file_language_map, file_labels_map, unknown_files, files_without_labels

def print_results(language_counter, labels_counter, file_language_map, file_labels_map, unknown_files, files_without_labels):
    """打印分析结果"""
    print("\n" + "="*60)
    print("编程语言和标签分布分析结果")
    print("="*60)
    
    total_files = sum(language_counter.values())
    
    print(f"\n总计文件数: {total_files}")
    
    # 语言分布
    print("\n语言分布:")
    print("-" * 40)
    for language, count in language_counter.most_common():
        percentage = (count / total_files) * 100
        print(f"{language:<20} {count:>6} ({percentage:>5.1f}%)")
    
    # 标签分布
    print("\n" + "="*60)
    print("标签分布:")
    print("-" * 40)
    
    if labels_counter:
        total_labels = sum(labels_counter.values())
        print(f"总计标签数: {total_labels}")
        print(f"唯一标签数: {len(labels_counter)}")
        print()
        
        for label, count in labels_counter.most_common():
            percentage = (count / total_labels) * 100
            print(f"{label:<25} {count:>6} ({percentage:>5.1f}%)")
    else:
        print("未找到任何标签")
    
    print("\n" + "="*60)
    
    # 显示未知语言的文件
    if unknown_files:
        print(f"\n未知语言的文件 ({len(unknown_files)} 个):")
        print("-" * 40)
        for filename, edited_file in unknown_files[:20]:  # 只显示前20个
            print(f"{filename}: {edited_file}")
        if len(unknown_files) > 20:
            print(f"... 还有 {len(unknown_files) - 20} 个文件")
    
    # 显示没有标签的文件
    if files_without_labels:
        print(f"\n没有标签的文件 ({len(files_without_labels)} 个):")
        print("-" * 40)
        for filename in files_without_labels[:20]:  # 只显示前20个
            print(f"{filename}")
        if len(files_without_labels) > 20:
            print(f"... 还有 {len(files_without_labels) - 20} 个文件")
    
    # 保存详细结果到JSON文件
    output_file = "language_and_labels_distribution_results.json"
    results = {
        'summary': {
            'total_files': total_files,
            'language_counts': dict(language_counter),
            'total_labels': sum(labels_counter.values()) if labels_counter else 0,
            'unique_labels': len(labels_counter),
            'labels_counts': dict(labels_counter)
        },
        'file_details': {
            'languages': file_language_map,
            'labels': file_labels_map
        },
        'unknown_files': unknown_files,
        'files_without_labels': files_without_labels
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细结果已保存到: {output_file}")

def main():
    """主函数"""
    # 设置train文件夹路径
    train_dir = "data/SFT/zeta/train"
    
    print("开始分析编程语言和标签分布...")
    print(f"分析目录: {train_dir}")
    
    # 分析语言分布和标签分布
    language_counter, labels_counter, file_language_map, file_labels_map, unknown_files, files_without_labels = analyze_language_and_labels_distribution(train_dir)
    
    # 打印结果
    print_results(language_counter, labels_counter, file_language_map, file_labels_map, unknown_files, files_without_labels)

if __name__ == "__main__":
    main()
