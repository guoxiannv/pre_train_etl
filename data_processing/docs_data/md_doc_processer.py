#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse, json, re, os
import textwrap
import hashlib
from pathlib import Path
from typing import List, Tuple

from tqdm import tqdm

SELECTED_LANGUAGES = ["javascript", "typescript", "js", "ts", "arkts"]

H_BLOCK = re.compile(r'^(#{1,6})\s+(.*)$')
CODE_FENCE = re.compile(r'^\s*```([^\s`]+)?\s*$')

# Simple bullets like "- [label] ...": capture prop lines
PROP_BULLET = re.compile(r'^\s*-\s*\[(\w+)\]\((.*?)\):\s*(.*)$')
PLAIN_BULLET = re.compile(r'^\s*-\s*(.*)$')

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                json_obj = json.loads(line)
                data.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
    return data

def write_jsonl(data:List[dict],file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in data:
            json.dump(item, file, ensure_ascii=False)  # ensure_ascii=False allows non-ASCII characters
            file.write('\n')

def write_json(data:List[dict],target_json):
    with open(target_json, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def hash_path(path: str) -> str:
    """Generate SHA1 hash of the given path."""
    return hashlib.sha1(path.encode('utf-8')).hexdigest()

def read_lines(p: Path) -> List[str]:
    try:
        return p.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as e:
        print(f"Skipping file due to decode error: {p}: {e}")
        return []

def clean_text(s: str) -> str:
    # Remove markdown links but keep the visible text: [text](url) -> text
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
    # Remove image tags ![...]([...])
    s = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', s)
    return s.strip()

def extract_blocks(lines: List[str]) -> List[Tuple[str, str, List[Tuple[str,str]]]]:
    """
    Return list of (section_title_hierarchy, doc_text, [code_blocks]) for each section.
    Each section title is the concatenation of its heading and all parent headings separated by '/'.
    """
    sections: List[Tuple[str, str, List[Tuple[str, str]]]] = []
    heading_stack: List[str] = []
    cur_title = ""
    cur_doc_lines: List[str] = []
    cur_code_blocks: List[Tuple[str, str]] = []

    def flush_section():
        nonlocal cur_title, cur_doc_lines, cur_code_blocks
        if cur_title or cur_doc_lines or cur_code_blocks:
            sections.append((cur_title, "\n".join(cur_doc_lines).strip(), cur_code_blocks.copy()))
        cur_title = ""
        cur_doc_lines.clear()
        cur_code_blocks.clear()

    in_code = False
    buf: List[str] = []
    code_lang: str

    for line in lines:
        mcode = CODE_FENCE.match(line)
        if mcode:
            if not in_code:
                in_code = True
                code_lang = (mcode.group(1) or "").lower()
                buf.clear()
            else:
                in_code = False
                cur_code_blocks.append((code_lang, "\n".join(buf)))
            continue

        if in_code:
            buf.append(line)
            continue

        mh = H_BLOCK.match(line)
        if mh:
            flush_section()
            level = len(mh.group(1))
            title = mh.group(2).strip()
            # adjust heading stack
            if len(heading_stack) >= level:
                heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            cur_title = " / ".join(heading_stack)
            continue

        cur_doc_lines.append(line)

    flush_section()
    return sections

def collect_global_props_events(doc_texts: List[str]) -> Tuple[List[str], List[str]]:
    props, events = [], []
    for doc in doc_texts:
        for line in doc.splitlines():
            m = PROP_BULLET.match(line)
            if m:
                name, _, desc = m.groups()
                props.append(f"- {name}: {desc}")
                continue
            if "onClick" in line or "onTouch" in line:
                m2 = PLAIN_BULLET.match(line)
                if m2:
                    events.append(f"- {m2.group(1)}")
    return sorted(set(props)), sorted(set(events))

def build_doc_text(section_title: str, summary: str,
                   props: List[str], events: List[str]) -> str:
    parts: List[str] = []
    if section_title:
        parts.append(f"Section: {section_title}")
    if summary.strip():
        parts.append("Summary:")
        parts.append(clean_text(summary))
    if props:
        parts.append("Props:")
        parts.extend(clean_text(p) for p in props)
    if events:
        parts.append("Events:")
        parts.extend(clean_text(e) for e in events)
    return "\n".join(parts)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root_dir", default="C:/Users\Yuhuai Liu\Downloads\docs-master\en", help="Root directory to scan for .md files")
    ap.add_argument("--project_name", default="docs", help="Project name to assign to each record")
    ap.add_argument("--out_doc", default="doc_inject.jsonl", help="Output JSONL for doc-inject records")
    ap.add_argument("--out_code", default="pure_code.jsonl", help="Output JSONL for pure-code records")
    ap.add_argument("--display_root_path", default="docs/en", help="root path to display in output records")
    args = ap.parse_args()

    root = Path(args.root_dir)
    doc_records: List[dict] = []
    code_records: List[dict] = []

    md_files = list(root.rglob("*.md"))
    for md_path in tqdm(md_files, desc="Scanning .md files"):
        rel_path = md_path.relative_to(root)
        # Skip release-notes folder
        if "release-notes" in str(rel_path).lower():
            continue
            
        rel_path_display = Path(args.display_root_path).joinpath(rel_path)
        lines = read_lines(md_path)
        sections = extract_blocks(lines)
        all_doc_texts = [doc for _, doc, _ in sections if doc]
        props, events = collect_global_props_events(all_doc_texts)

        for section_idx, (title, doc_text, code_blocks) in enumerate(sections):
            doc_text_clean = clean_text(doc_text)
            for code_idx, (lang, code) in enumerate(code_blocks):
                if not code.strip() or lang not in SELECTED_LANGUAGES:
                    continue
                code_clean = textwrap.dedent(code).strip()
                
                # Create unique ID by combining path, section index, and code index
                unique_suffix = f"{section_idx}_{code_idx}_{hash_path(code_clean)[:8]}"
                
                # Doc-inject entry
                doc_records.append({
                    "id": f'doc_inject:{hash_path(str(rel_path_display))}_{unique_suffix}',
                    "project_name": args.project_name,
                    "path": str(rel_path_display),
                    "text": f"<DOC>\n{build_doc_text(title, doc_text_clean, props, events)}\n</DOC>\n<CODE>\n{code_clean}\n</CODE>"
                })
                # Pure-code entry
                code_records.append({
                    "id": f'pure_code:{hash_path(str(rel_path_display))}_{unique_suffix}',
                    "project_name": args.project_name,
                    "path": str(rel_path_display),
                    "text": code_clean
                })
    # Write outputs
    write_jsonl(code_records, args.out_code)
    write_jsonl(doc_records, args.out_doc)
    write_json(doc_records, Path(args.out_doc).with_suffix('.json'))
    write_json(code_records, Path(args.out_code).with_suffix('.json'))

if __name__ == "__main__":
    main()
