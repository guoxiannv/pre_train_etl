#!/usr/bin/env python3
"""
统计指定目录下每个 JSONL 文件内：
1) repoUrl 为空/缺失 的数量（逐文件统计并输出数字）
2) 使用每条记录的 project_name 与 arkts_repos.json 的 git_url 进行“包含匹配”（git_url 包含 project_name 即视为匹配），统计未匹配的数量，并导出未匹配的 project_name 清单文件（逐文件输出）。

用法:
  python check_repo_urls.py --input-dir <目录> --repos-file <arkts_repos.json>
默认 input-dir 为脚本同级的 trans_text_data，默认 repos-file 为脚本同级的 arkts_repos.json。
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Set, Tuple, List


def load_repo_git_urls(repos_file: Path) -> List[str]:
    """
    从 arkts_repos.json 加载 git_url 列表。
    支持两种数据结构：
      - 列表: [{"git_url": "..."}, ...]
      - 字典: {"repos": [{"git_url": "..."}, ...]}
    """
    if not repos_file.exists():
        print(f"❌ repos 文件不存在: {repos_file}")
        return []
    try:
        with open(repos_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('repos', data) if isinstance(data, dict) else data
        urls: List[str] = []
        for it in (items or []):
            if isinstance(it, dict):
                url = str(it.get('git_url', '') or '').strip()
                if url:
                    urls.append(url)
        return urls
    except Exception as e:
        print(f"❌ 读取 repos 文件失败: {e}")
        return []


def iter_jsonl_records(file_path: Path):
    """逐行读取 JSONL 记录，解析失败的行跳过。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    print(f"   ⚠️ JSON解析失败，文件 {file_path.name} 第{line_num}行，已跳过")
                    continue
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")


def analyze_file(jsonl_file: Path, repo_git_urls: List[str]) -> Tuple[int, int, Set[str], int]:
    """
    分析单个 JSONL 文件：
    返回: (total_records, missing_repo_url_count, unmatched_project_names(去重), unmatched_count(未匹配记录条数))
    """
    total_records = 0
    missing_repo_url = 0
    unmatched_project_names: Set[str] = set()
    unmatched_count = 0

    for rec in iter_jsonl_records(jsonl_file):
        total_records += 1
        # 1) 统计 repoUrl 为空/缺失
        repo_url = str(rec.get('repoUrl') or '').strip()
        if not repo_url:
            missing_repo_url += 1
        # 2) project_name 与 git_url(包含匹配)，按 '-' 逐个替换尝试
        project_name = str(rec.get('project_name') or '').strip()
        if project_name:
            matched = False
            # 原始匹配
            for url in repo_git_urls:
                if url and project_name in url:
                    matched = True
                    break
            # 逐个 '-' 替换为 '/' 再匹配
            if not matched and '-' in project_name:
                hyphen_positions = [i for i, ch in enumerate(project_name) if ch == '-']
                for pos in hyphen_positions:
                    alt_name = project_name[:pos] + '/' + project_name[pos+1:]
                    for url in repo_git_urls:
                        if url and alt_name in url:
                            matched = True
                            break
                    if matched:
                        break
            if not matched:
                unmatched_project_names.add(project_name)
                unmatched_count += 1

    return total_records, missing_repo_url, unmatched_project_names, unmatched_count


def main():
    parser = argparse.ArgumentParser(description='逐文件统计 repoUrl 为空数量与 project_name 与 git_url 的包含匹配未命中清单')
    curdir = Path(__file__).parent
    parser.add_argument('--input-dir', default=str(curdir / 'trans_text_data'), help='输入目录(默认: 脚本同级 trans_text_data)')
    parser.add_argument('--repos-file', default=str(curdir / 'arkts_repos.json'), help='repos文件路径(默认: 脚本同级 arkts_repos.json)')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    repos_file = Path(args.repos_file)

    if not input_dir.exists():
        print(f"❌ 输入目录不存在: {input_dir}")
        return

    repo_git_urls = load_repo_git_urls(repos_file)
    print(f"加载 git_url 数量: {len(repo_git_urls)} 来自 {repos_file}")

    jsonl_files = list(input_dir.glob('*.jsonl'))
    if not jsonl_files:
        print(f"❌ 未在 {input_dir} 找到任何 JSONL 文件")
        return

    print(f"在 {input_dir} 发现 {len(jsonl_files)} 个 JSONL 文件")

    # 汇总统计
    grand_total = 0
    grand_missing = 0
    grand_unmatched_projects: Set[str] = set()

    for idx, fp in enumerate(jsonl_files, 1):
        print(f"\n📄 处理文件 {idx}/{len(jsonl_files)}: {fp.name}")
        total, missing_cnt, unmatched_projects, unmatched_count = analyze_file(fp, repo_git_urls)

        # 控制台打印每文件统计（不输出文件）
        print(f"   repoUrl 为空数量: {missing_cnt}")
        print(f"   未匹配的 project_name: {len(unmatched_projects)} (记录条数: {unmatched_count})")

        # 汇总
        grand_total += total
        grand_missing += missing_cnt
        grand_unmatched_projects.update(unmatched_projects)

    # 目录级总结与未匹配清单导出（汇总一个文件）
    print("\n" + "=" * 60)
    print("统计完成 (目录级)")
    print(f"总记录数: {grand_total}")
    print(f"repoUrl 缺失/为空(合计): {grand_missing}")
    print(f"project_name 与 git_url(包含匹配)未匹配(去重, 合计): {len(grand_unmatched_projects)}")

    # 汇总生成一个未匹配文件
    if grand_unmatched_projects:
        out_all = input_dir / 'unmatched_project_names.txt'
        try:
            with open(out_all, 'w', encoding='utf-8') as f:
                for name in sorted(grand_unmatched_projects):
                    f.write(name + '\n')
            print(f"未匹配的 project_name 清单(汇总)已导出: {out_all} (共 {len(grand_unmatched_projects)} 个)")
        except Exception as e:
            print(f"❌ 导出汇总未匹配清单失败: {e}")


if __name__ == '__main__':
    main() 