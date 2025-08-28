import os
import json
import pickle
import sys
import uuid
import hashlib
from tqdm import tqdm
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import *


def find_and_read_ets_files(root_dir):
    """
    Recursively finds all .ets files in a directory, reads their content,
    and captures their relative path and first-level subfolder.

    Args:
        root_dir (str): The absolute or relative path to the data directory.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              relative_path, first_level_subfolder, and content of an .ets file.
              Returns an empty list if the directory does not exist.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Directory not found at '{root_dir}'")
        return []

    json_list = []
    print(f"Starting scan in directory: {os.path.abspath(root_dir)}")
    
    # Count total directories for progress bar
    total_dirs = sum(1 for _ in os.walk(root_dir))
    
    with tqdm(total=total_dirs, desc="Scanning directories", unit="dir") as pbar:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                # Check if the file is an .ets file
                if filename.endswith(".ets"):
                    # --- This entire block only runs for .ets files ---

                    full_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(full_path, root_dir)

                    path_parts = relative_path.split(os.sep)
                    first_level_subfolder = path_parts[0] if len(path_parts) > 1 else None

                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Could not read file {full_path}: {e}")
                        content = f"Error reading file: {e}"
                    
                    stable_id = hashlib.sha256(relative_path.encode('utf-8')).hexdigest()

                    # Create the dictionary for this file's data
                    record = {
                        "path": relative_path,
                        "project_name": first_level_subfolder,
                        "text": content,
                        "id":stable_id,
                    }

                    # **THE FIX**: Append the record immediately after creating it,
                    # still inside the if block.
                    json_list.append(record)
            
            pbar.update(1)
    
    return json_list


# --- How to use the function ---
if __name__ == "__main__":
    # IMPORTANT: Replace this with the path to your actual data directory
    current_dir = os.path.dirname(__file__)
    data_directory = os.path.join(current_dir, "../ArktsRepos")

    # Process the files
    ets_data = find_and_read_ets_files(data_directory)

    # with open("./tmp.pkl", "wb") as f:
    #     pickle.dump(ets_data, f)

    if ets_data:
        # Define the output file name
        output_filename = os.path.join(current_dir, "../data_processing/code_data/raw_data/dz5484")

        write_jsonl(ets_data, output_filename + ".jsonl")

        print(f"\nSuccessfully processed {len(ets_data)} .ets files.")
        print(f"Results have been saved to '{output_filename}'")
    else:
        print("\nNo .ets files were found or the directory was invalid.")