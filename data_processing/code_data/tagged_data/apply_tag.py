import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
# Add the parent directory to sys.path to import utils and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils import read_jsonl, write_jsonl, read_json
SCRIPT_DIR = Path(__file__).parent


if __name__ == "__main__":
    # Load data
    test_data = read_jsonl(SCRIPT_DIR / "../cleaned_data/test.jsonl")
    tagged_data = read_jsonl(SCRIPT_DIR / "../tagged_data/formatted_data.jsonl")
    
    # build map
    text_tag_map = {}
    for data in tagged_data:
        text_tag_map[data["text"]] = data
    
    # apply tag
    # apply_fields = ["replica", "decision", "labels", "arkts_score", "quality_score", "confidence", "rationale", "model", "temperature", "prompt_tokens", "completion_tokens", "total_tokens", "raw_prompt", "raw_response"]
    apply_fields = ["llm_formatted"]
    applied_count = 0
    for data in test_data:
        text_field = data["text"]
        if text_field in text_tag_map:
            # apply fields
            for field in apply_fields:
                if field in text_tag_map[text_field]:
                    data[field] = text_tag_map[text_field][field]
                    applied_count += 1
    
    # Simple statistics
    print(f"Total test records: {len(test_data)}")
    print(f"Total tagged records: {len(tagged_data)}")
    print(f"Records with tags applied: {sum(1 for data in test_data if data['text'] in text_tag_map)}")
    print(f"Total field values applied: {applied_count}")
    
    # write to file
    output_file = SCRIPT_DIR / "../tagged_data/test_llm_formatted.jsonl"
    write_jsonl(test_data, output_file)
    print(f"Output written to: {output_file}")
    
    