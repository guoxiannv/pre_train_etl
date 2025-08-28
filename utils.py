import json
from pathlib import Path
from typing import List, Any

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

def read_json(file_path) -> Any:
    """Read a JSON file and return its content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_jsonl(data:List[dict],file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in data:
            json.dump(item, file, ensure_ascii=False)  # ensure_ascii=False allows non-ASCII characters
            file.write('\n')

def write_json(data:List[dict],target_json):
    with open(target_json, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # For test only
    data = read_jsonl("./data_processing/code_data/tagged_data/results_with_tokens.jsonl")
    print("data loaded")
    leaked = [i for i in data if i["leaked"]==True]