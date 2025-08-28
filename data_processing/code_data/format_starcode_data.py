import json
import uuid
import os
from pathlib import Path

def format_starcode_to_custom(input_file, output_file):
    """
    Convert StarCoder format JSONL to custom format
    
    StarCoder format:
    {
        "max_stars_repo_path": "path/to/file",
        "max_stars_repo_name": "repo_name", 
        "max_stars_count": 123,
        "id": "original_id",
        "content": "file_content"
    }
    
    Custom format:
    {
        "path": "relative_path",
        "project_name": "first_level_subfolder", 
        "text": "content",
        "id": "project_name:relative_path:uuid"
    }
    """
    
    processed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            try:
                # Parse the StarCoder format JSON
                starcode_data = json.loads(line.strip())
                
                # Extract fields from StarCoder format
                repo_path = starcode_data.get('max_stars_repo_path', '')
                repo_name = starcode_data.get('max_stars_repo_name', '')
                content = starcode_data.get('content', '')
                
                # Skip empty content
                if not content.strip():
                    continue
                
                # Extract project name (first part of repo name or repo name itself)
                if '/' in repo_name:
                    project_name = repo_name.split('/')[1]  # Take the second part after username
                else:
                    project_name = repo_name
                
                # Use the repo path as relative path
                relative_path = repo_path
                
                # Create the custom format record
                record = {
                    "path": relative_path,
                    "project_name": project_name,
                    "text": content,
                    "id": f'{project_name}:{relative_path}:{uuid.uuid4()}'
                }
                
                # Write to output file
                outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
                processed_count += 1
                
                # Progress indicator
                if processed_count % 10000 == 0:
                    print(f"Processed {processed_count} records...")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue
    
    print(f"\nConversion completed! Processed {processed_count} records.")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    input_file = "D:\\Documents\\PythonProject\\pretrain_etl\\code_data\\ts_data\\filtered_starcode_ts.jsonl"
    output_file = "D:\\Documents\\PythonProject\\pretrain_etl\\code_data\\ts_data\\formatted_starcode_ts.jsonl"
    
    print(f"Converting StarCoder format data...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    format_starcode_to_custom(input_file, output_file)
    # Read first two lines of formatted output
    # output_file = "D:\\Documents\\PythonProject\\pretrain_etl\\code_data\\ts_data\\formatted_starcode.jsonl"
    # with open(output_file, 'r', encoding='utf-8') as f:
    #     for i, line in enumerate(f):
    #         if i < 2:
    #             data = json.loads(line)
    #             print(line.strip())
    #         else:
    #             break
