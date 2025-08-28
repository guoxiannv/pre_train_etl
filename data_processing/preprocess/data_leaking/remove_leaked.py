import multiprocessing
import sys
import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm

# 定义当前脚本路径
SCRIPT_DIR = Path(__file__).parent.absolute()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils import *


IGNORE_DIR = ["entry", "features", "commons", "\\"]

def normalize_text(s: str) -> str:
    """
    规范化字符串：转为小写，并移除 '-' 和 '_'
    """
    return s.lower().replace('-', '').replace('_', '')


def is_item_leaked(item: dict, leaked_set_norm: set) -> bool:
    """Return True if the item is considered leaked based on its path; False otherwise."""
    try:
        normalized_path = os.path.normpath(item["path"])  # type: ignore[index]
        file_path_components = normalized_path.split(os.path.sep)

        # If path is too short, treat it as non-leaked to be permissive
        if len(file_path_components) < 3:
            return False

        file_path_suffix = "/".join(file_path_components[:3])
        file_path_suffix_norm = normalize_text(file_path_suffix)

        return any(leak in file_path_suffix_norm for leak in leaked_set_norm)
    except (KeyError, TypeError):
        # Malformed item; treat as non-leaked in tagging and allow in cleaning
        return False


def check_item_for_leaks(item: dict, leaked_set_norm: set) -> dict | None:
    """
    Worker function to check a single item for leaks.
    Returns the item if it's clean, otherwise returns None.
    """
    if not is_item_leaked(item, leaked_set_norm):
        return item
    return None


def tag_item_with_leak(item: dict, leaked_set_norm: set) -> Dict[str, Any]:
    """Return a shallow copy of the item with an added 'leaked': bool field."""
    # Avoid mutating the original
    tagged_item: Dict[str, Any] = dict(item) if isinstance(item, dict) else {"value": item}
    tagged_item["leaked"] = is_item_leaked(tagged_item, leaked_set_norm)
    return tagged_item


def tag_llm_judgements_with_leaks(judgements_data: List[Dict[str, Any]], leaked_set_norm: set) -> List[Dict[str, Any]]:
    """
    Tag LLM judgements with leaked boolean field.
    
    Args:
        judgements_data: List of LLM judgement dictionaries
        leaked_set_norm: Set of normalized leaked repository names
    
    Returns:
        List of judgements with added 'leaked' field
    """
    print(f"Starting leak detection for {len(judgements_data)} LLM judgements...")
    
    tagged_results = []
    leaked_count = 0
    
    for item in judgements_data:
        item_copy = item.copy()
        is_leaked = is_item_leaked(item_copy, leaked_set_norm)
        item_copy['leaked'] = is_leaked
        if is_leaked:
            leaked_count += 1
        tagged_results.append(item_copy)
    
    print(f"Leak detection completed: {leaked_count} items marked as leaked out of {len(judgements_data)} total")
    return tagged_results


def main():
    """Main function to orchestrate the data loading, processing, and writing."""
    # Use as many processes as there are CPU cores for maximum performance
    num_processes = multiprocessing.cpu_count()
    print(f"Starting parallel processing with {num_processes} workers...")
    # 1. Load data (I/O is best done in the main process)
    print("Loading data...")
    # full_train_data = read_jsonl(SCRIPT_DIR / "../../code_data/cleaned_data/arkts_pretrain_50k_leaked.jsonl")
    leaked = read_json(SCRIPT_DIR / "test_repo_list.json")
    leaked_set_norm = {normalize_text(name) for name in leaked}

    # print(f"before clean: {len(full_train_data)} datapoints")

    # # 2. Process data in parallel
    # second_filtered_train_data = []

    # # Use functools.partial to "freeze" the leaked_set_norm argument for the worker function.
    # # This is a clean way to pass constant data to the pool workers.
    # worker_func = partial(check_item_for_leaks, leaked_set_norm=leaked_set_norm)

    # # The 'with' statement ensures the pool is properly cleaned up
    # with multiprocessing.Pool(processes=num_processes) as pool:
    #     # pool.imap_unordered is highly efficient for this task. It applies the function
    #     # to the data and returns results as soon as they are finished, in any order.
    #     # We use a chunksize to reduce overhead of sending tasks to worker processes.
    #     results_iterator = pool.imap_unordered(worker_func, full_train_data, chunksize=250)

    #     # Collect non-None results from the iterator into the final list
    #     # tqdm shows a progress bar for the operation.
    #     second_filtered_train_data = [
    #         item for item in tqdm(results_iterator, total=len(full_train_data)) if item is not None
    #     ]

    # print(f"after clean: {len(second_filtered_train_data)} datapoints")

    # # 3. Write results (I/O is done in the main process)
    # print("Writing cleaned data to files...")
    # write_jsonl(second_filtered_train_data, SCRIPT_DIR / "../code_data/cleaned_data/arkts_pretrain_50k_rm_leak.jsonl")
    # write_json(second_filtered_train_data, SCRIPT_DIR / "../code_data/cleaned_data/arkts_pretrain_50k_rm_leak.json")

    # 4. Tag LLM judgements with leaked boolean and write results
    print("\nLoading LLM judgements for tagging...")
    judgements_path = SCRIPT_DIR / "../../code_data/tagged_data/LLM_tagged/judgements.jsonl"
    if os.path.exists(judgements_path):
        llm_judgements = read_jsonl(judgements_path)
        print(f"loaded {len(llm_judgements)} LLM judgements")

        print("Starting parallel tagging of LLM judgements...")
        # tag_worker = partial(tag_item_with_leak, leaked_set_norm=leaked_set_norm) # This line is no longer needed

        # with multiprocessing.Pool(processes=num_processes) as pool: # This block is no longer needed
        #     tagged_iterator = pool.imap_unordered(tag_worker, llm_judgements, chunksize=250)
        #     tagged_results = [item for item in tqdm(tagged_iterator, total=len(llm_judgements))]

        tagged_llm_judgements = tag_llm_judgements_with_leaks(llm_judgements, leaked_set_norm)

        results_path = SCRIPT_DIR / "../../code_data/tagged_data/results.jsonl"
        os.makedirs(results_path.parent, exist_ok=True)
        print(f"Writing tagged LLM results to {results_path} ...")
        write_jsonl(tagged_llm_judgements, results_path)
        print("Tagged LLM results written.")
    else:
        print(f"LLM judgements file not found at {judgements_path}, skipping tagging step.")

    print("done")


# This is crucial for multiprocessing. It prevents child processes from
# re-importing and re-executing the main script's code upon creation.
if __name__ == "__main__":
    main()