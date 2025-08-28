#!/usr/bin/env python3
"""
根据 arkts_repos.json 为指定 JSONL 数据补充 api_ver 字段：
- 从 arkts_repos.json 中拼接 key: "repo_name~author~id"
- 将该 key 与目标 JSONL 每条记录的 project_name 做“精确匹配”
- 命中则把对应的 api_ver 写入记录为 record['api_ver']
- 输出带 api_ver 的新 JSONL；并在控制台统计未写入 api_ver 的记录条数

用法：
  python add_api_ver_from_repos.py --repos-file <arkts_repos.json> --input-jsonl <data.jsonl> --output-jsonl <out.jsonl>
默认：
  --repos-file 为脚本同级 arkts_repos.json
  --output-jsonl 默认为 <input-jsonl> 同目录下追加后缀 _with_api_ver.jsonl
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_repos_mapping(repos_file: Path) -> Dict[str, Any]:
    """
    加载 arkts_repos.json，构建 id -> api_ver 的映射。
    支持两种结构：
      - 列表: [{"repo_name": ..., "author": ..., "id": ..., "api_ver": ...}, ...]
      - 字典: {"repos": [ ... 如上 ... ]}
    """
    if not repos_file.exists():
        raise FileNotFoundError(f"repos 文件不存在: {repos_file}")
    with open(repos_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('repos', data) if isinstance(data, dict) else data
    mapping: Dict[str, Any] = {}
    if not isinstance(items, list):
        return mapping
    for it in items:
        if not isinstance(it, dict):
            continue
        rid = str(it.get('id', '') or '').strip()
        if not rid:
            continue
        api_ver = it.get('api_ver')
        mapping[rid] = api_ver
    return mapping


def process_jsonl(input_jsonl: Path, output_jsonl: Path, key_to_api: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    读取 input_jsonl，匹配并补充 api_ver，写入 output_jsonl。
    返回 (total, matched, missing_api_ver_after)
    """
    total = 0
    matched = 0
    missing_after = 0

    # 确保输出目录存在
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(input_jsonl, 'r', encoding='utf-8') as fin, open(output_jsonl, 'w', encoding='utf-8') as fout:
        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # 跳过损坏行
                continue
            total += 1

            # 若已有 api_ver 则保留；否则尝试补充
            if 'api_ver' not in rec:
                proj = str(rec.get('project_name', '') or '').strip()
                if proj:
                    # 用 project_name 与 repos 中的 id 做包含匹配
                    for rid, api_ver in key_to_api.items():
                        if rid and proj and rid in proj:
                            rec['api_ver'] = api_ver
                            matched += 1
                            break

            # 统计仍无 api_ver 的记录
            if 'api_ver' not in rec:
                missing_after += 1

            json.dump(rec, fout, ensure_ascii=False)
            fout.write('\n')

    return total, matched, missing_after


def main():
    parser = argparse.ArgumentParser(description='用 arkts_repos.json 为指定 JSONL 追加 api_ver 字段')
    curdir = Path(__file__).parent
    parser.add_argument('--repos-file', default=str(curdir / 'arkts_repos.json'), help='repos 文件路径')
    parser.add_argument('--input-jsonl', required=True, help='待补充的 JSONL 文件路径')
    parser.add_argument('--output-jsonl', help='输出 JSONL 文件路径（默认: 同目录追加 _with_api_ver 后缀）')
    args = parser.parse_args()

    repos_file = Path(args.repos_file)
    input_jsonl = Path(args.input_jsonl)
    if not input_jsonl.exists():
        raise FileNotFoundError(f"输入 JSONL 不存在: {input_jsonl}")

    # 计算默认输出路径
    output_jsonl = Path(args.output_jsonl) if args.output_jsonl else input_jsonl.with_name(f"{input_jsonl.stem}_with_api_ver{input_jsonl.suffix}")

    # 加载映射
    key_to_api = load_repos_mapping(repos_file)
    print(f"加载 repos 映射数量: {len(key_to_api)}")

    total, matched, missing_after = process_jsonl(input_jsonl, output_jsonl, key_to_api)

    print("\n=== 处理完成 ===")
    print(f"输入记录数: {total}")
    print(f"匹配并写入 api_ver 条数: {matched}")
    print(f"最终未含 api_ver 的记录条数: {missing_after}")
    print(f"输出文件: {output_jsonl}")


if __name__ == '__main__':
    main() 