import json
from pathlib import Path
from typing import List
import uuid
import os

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


if __name__ == '__main__':
    curdir = os.path.dirname(__file__)
    # raw_4k = read_jsonl("../arkui_2k_pretrain_cleaned.jsonl")
    # formated_4k = []
    # for item in raw_4k:
    #     formated_item = {"text": item["text"]}
    #     path_split = item["path"].split("{}\\".format(item["project_name"]))
    #     formated_item["path"] = str(Path(item["project_name"]).joinpath(path_split[-1]))
    #     formated_item["project_name"] = item["project_name"]
    #     formated_item["id"] = f'{item["project_name"]}:{formated_item["path"]}:{uuid.uuid4()}'
    #     formated_4k.append(formated_item)
    # write_jsonl(formated_4k, "../cleaned_data/arkui_2k_pretrain_cleaned_formated.jsonl")


    harmony_samples = read_jsonl(os.path.join(curdir,"./harmony_samples_raw.jsonl"))
    formated_data = []
    for sample in harmony_samples:
        formated_sample = {}
        for key, value in sample.items():
            if key == "relative_path":
                formated_sample["path"] = value
            else:
                formated_sample[key] = value
        formated_sample["id"] = f'{formated_sample["project_name"]}:{formated_sample["path"]}:{uuid.uuid4()}'
        formated_data.append(formated_sample)
    write_jsonl(formated_data, os.path.join(curdir,"./harmony_samples_formated_data.jsonl"))

    # dz1040 = read_jsonl("./code_data/raw_data/dz1040.jsonl")
    # formated_dz1040 = []
    # for item in dz1040:
    #     formated_item = {
    #         "text": item["text"],
    #         "path": item["path"],
    #         "project_name": item["project_name"],
    #         "id": f'{item["project_name"]}:{item["path"]}:{uuid.uuid4()}',
    #     }
    #     formated_dz1040.append(formated_item)
    # write_jsonl(formated_dz1040, "./code_data/raw_data/dz1040_formated.jsonl")
