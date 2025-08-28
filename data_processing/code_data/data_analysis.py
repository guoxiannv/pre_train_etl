import json
from typing import List, Dict
import matplotlib.pyplot as plt
import os

current_file_path = os.path.abspath(__file__)

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
    
def compare_length_distribution(data1: List[Dict], data2: List[Dict]):
    """
    Compare the length distribution of two datasets and plot the results.
    
    Args:
        data1 (List[Dict]): First dataset.
        data2 (List[Dict]): Second dataset.
    """
    lengths1 = [len(item['text']) for item in data1]
    lengths2 = [len(item['text']) for item in data2]

    plt.figure(figsize=(12, 6))
    plt.hist(lengths1, bins=50, alpha=0.5, label='Dataset 1', color='blue')
    plt.hist(lengths2, bins=50, alpha=0.5, label='Dataset 2', color='orange')
    plt.xlabel('Length of text')
    plt.ylabel('Frequency')
    plt.title('Length Distribution Comparison')
    plt.legend()
    plt.show()

def get_diff_item(data1: List[Dict], data2: List[Dict]) -> List[Dict]:
    """
    Get items that are in data1 but not in data2.
    
    Args:
        data1 (List[Dict]): First dataset.
        data2 (List[Dict]): Second dataset.
        
    Returns:
        List[Dict]: Items that are in data1 but not in data2.
    """
    set_data2 = {item["path"] for item in data2}
    set_data1 = {item["path"] for item in data1}
    diff_items = [item for item in data2 if item["path"] not in set_data1]
    write_jsonl(diff_items, "diff.jsonl")
    return diff_items


if __name__ == "__main__":
    arkui_2k = read_jsonl("./FinetuneZeta/Data/OpenSourceData/pretrain_zeta_data/4k_file_cleaned_3k.jsonl")
    arkui_4k = read_jsonl("./FinetuneZeta/Data/OpenSourceData/pretrain_zeta_data/4k_origin_file.jsonl")
    diff_items = get_diff_item(arkui_2k, arkui_4k)
    compare_length_distribution(arkui_2k, arkui_4k)
