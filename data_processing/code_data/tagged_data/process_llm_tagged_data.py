# This script processes judgements.jsonl to create a complete data processing pipeline
# Includes: data separation, leak detection, token counting, and extensible structure
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import random

# Add the parent directory to sys.path to import utils and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils import read_jsonl, write_jsonl, read_json
from data_processing.preprocess.data_leaking.remove_leaked import is_item_leaked, normalize_text, tag_llm_judgements_with_leaks
from analysis.calculate_tokens import calculate_tokens_for_jsonl

SCRIPT_DIR = Path(__file__).parent

def random_token_sample(
    items: List[Dict[str, Any]],
    target_tokens: int,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Randomly sample from items until cumulative text_tokens >= target_tokens.
    Returns (selected, remaining).
    Not strictly equal to target_tokens, stops as soon as >= target_tokens.
    """
    if target_tokens <= 0 or not items:
        return [], items[:]

    rng = random.Random(seed)
    shuffled = items[:]
    rng.shuffle(shuffled)

    selected = []
    total_tokens = 0

    for it in shuffled:
        selected.append(it)
        total_tokens += int(it.get("text_tokens", 0) or 0)
        if total_tokens >= target_tokens:
            break

    selected_set = set(map(id, selected))
    remaining = [it for it in items if id(it) not in selected_set]

    return selected, remaining

class DataProcessingPipeline:
    """Main pipeline class for processing judgements data"""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.setup_paths()
        
    def setup_paths(self):
        """Setup all input and output paths"""
        self.input_path = self.workspace_root / 'out_rounds/judgements_partially_formatted.jsonl'
        self.output_path = self.workspace_root / 'data_processing/code_data/tagged_data/judgements_partially_formatted.jsonl'
        self.output_removed_path = self.workspace_root / 'data_processing/code_data/tagged_data/removed_judgements.jsonl'
        self.output_kept_with_tag_path = self.workspace_root / 'data_processing/code_data/tagged_data/kept_with_tag_judgements.jsonl'
        self.output_kept_all_path = self.workspace_root / 'data_processing/code_data/tagged_data/kept_all_judgements.jsonl'
        self.output_leaked_tagged_path = self.workspace_root / 'data_processing/code_data/tagged_data/kept_all_leaked_tagged.jsonl'
        self.output_final_path = self.workspace_root / 'data_processing/code_data/tagged_data/kept_all_final.jsonl'
        self.output_split_path = self.workspace_root / 'data_processing/code_data/tagged_data/kept_all_with_split.jsonl'
        self.output_valid_path = self.workspace_root / 'data_processing/code_data/split_data/L2R_valid.jsonl'
        self.output_test_path = self.workspace_root / 'data_processing/code_data/split_data/L2R_test.jsonl'
        self.output_train_path = self.workspace_root / 'data_processing/code_data/split_data/L2R_train_{size}k.jsonl'

    def step1_separate_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Step 1: Separate data by decision and remove item_id"""
        print("=== Step 1: Separating data by decision ===")
        
        # Read the data
        print("Reading judgements data...")
        data = read_jsonl(self.input_path)
        print(f"Loaded {len(data)} entries")
        
        # Remove item_id column and sort by project_name
        processed_data = []
        for item in data:
            # Create a copy without item_id
            if 'item_id' in item:
                item_copy = {k: v for k, v in item.items() if k != 'item_id'}
            else:
                item_copy = item.copy()
            processed_data.append(item_copy)
        
        # Sort by project_name
        processed_data.sort(key=lambda x: x.get('project_name', ''))
        print("Data sorted by project_name")
        write_jsonl(processed_data, self.output_path)
        
        # Separate data by decision
        removed_data = []
        kept_with_tag_data = []
        kept_all_data = []
        
        for item in processed_data:
            decision = item.get('decision', '')
            if decision == 'REMOVE':
                removed_data.append(item)
            elif decision == 'KEEP_WITH_TAG':
                kept_with_tag_data.append(item)
                kept_all_data.append(item)
            elif decision == 'KEEP':
                kept_all_data.append(item)
        
        print(f"Found {len(removed_data)} entries with decision 'REMOVE'")
        print(f"Found {len(kept_with_tag_data)} entries with decision 'KEEP_WITH_TAG'")
        print(f"Found {len(kept_all_data)} entries with decision 'KEEP' or 'KEEP_WITH_TAG'")
        
        # Write separate files
        print("Writing removed_judgements.jsonl...")
        write_jsonl(removed_data, self.output_removed_path)
        
        print("Writing kept_with_tag_judgements.jsonl...")
        write_jsonl(kept_with_tag_data, self.output_kept_with_tag_path)
        
        print("Writing kept_all_judgements.jsonl...")
        write_jsonl(kept_all_data, self.output_kept_all_path)
        
        return {
            'removed': removed_data,
            'kept_with_tag': kept_with_tag_data,
            'kept_all': kept_all_data
        }
    
    def step2_detect_leaks(self, kept_all_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 2: Detect leaks in kept_all_data and add leaked field"""
        print("\n=== Step 2: Detecting data leaks ===")
        
        # Load leaked repository list
        leaked_repos_path = self.workspace_root / 'data_processing/preprocess/data_leaking/test_repo_list.json'
        if not leaked_repos_path.exists():
            print(f"Warning: Leaked repos file not found at {leaked_repos_path}")
            print("Skipping leak detection, all items marked as non-leaked")
            leaked_set_norm = set()
        else:
            leaked = read_json(leaked_repos_path)
            leaked_set_norm = {normalize_text(name) for name in leaked}
            print(f"Loaded {len(leaked_set_norm)} leaked repository patterns")
        
        # Use the reusable function from remove_leaked.py
        leaked_tagged_data = tag_llm_judgements_with_leaks(kept_all_data, leaked_set_norm)
        
        # Write leaked-tagged data
        write_jsonl(leaked_tagged_data, self.output_leaked_tagged_path)
        print(f"Leaked-tagged data saved to {self.output_leaked_tagged_path}")
        
        return leaked_tagged_data
    
    def step3_count_tokens(self, leaked_tagged_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 3: Count tokens for each item and add text_tokens field"""
        print("\n=== Step 3: Counting tokens ===")
        
        # Create temporary file for token counting
        temp_input_path = self.output_leaked_tagged_path
        temp_output_path = self.output_final_path
        
        print("Starting token counting process...")
        results = calculate_tokens_for_jsonl(str(temp_input_path), str(temp_output_path))
        
        if results.get("success"):
            print("Token counting completed successfully!")
            print(f"Total tokens: {results['total_tokens']:,}")
            print(f"Average tokens per entry: {results['average_tokens_per_entry']}")
            
            # Read the final processed data
            final_data = read_jsonl(temp_output_path)
            return final_data
        else:
            print(f"Token counting failed: {results.get('error', 'Unknown error')}")
            # Return original data if token counting fails
            return leaked_tagged_data
    
    def step4_make_split(self, final_data: List[Dict[str, Any]], test_target_tokens: int = 1_000_000, valid_target_tokens: int = 100_000) -> List[Dict[str, Any]]:
        """Step 4: Make train/test split and reorganize data"""
        print("\n=== Step 4: Making train/test split ===")
        
        # Separate data into train and test splits
        train_data = []
        unused_data = []
        
        for item in final_data:
            item_copy = item.copy()
            if item.get('leaked', False):
                # Mark leaked data as test split
                item_copy['split'] = 'unused'
                unused_data.append(item_copy)
            else:
                # Mark non-leaked data as train split
                item_copy['split'] = 'train'
                train_data.append(item_copy)
        
        print(f"Train split: {len(train_data)} entries")
        print(f"Unused split: {len(unused_data)} entries")
        
        # Sample test
        print(f"Random sampling TEST to >= {test_target_tokens:,} tokens...")
        test_selected, unused_remaining = random_token_sample(unused_data, target_tokens=test_target_tokens, seed=42)
        for it in test_selected:
            it['split'] = 'test'

        # Sample valid
        print(f"Random sampling VALID to >= {valid_target_tokens:,} tokens...")
        valid_selected, unused_rest = random_token_sample(unused_remaining, target_tokens=valid_target_tokens, seed=43)
        for it in valid_selected:
            it['split'] = 'valid'

        # Reorganize: train first, then unused, then valid, and test at the very end
        reorganized_data = train_data + valid_selected + test_selected + unused_rest

        return reorganized_data

    def step5_save_split_data(self, all_data: List[Dict[str, Any]], size_list: List[int] = [1_000_000, 20_000_000, 50_000_000]):
        """Step 5: Save all split data to split_data directory"""
        print("\n=== Step 5: Saving all split data ===")
        
        # Separate data by split
        train_data = [item for item in all_data if item['split'] == 'train']
        valid_data = [item for item in all_data if item['split'] == 'valid']
        test_data = [item for item in all_data if item['split'] == 'test']
        unused_data = [item for item in all_data if item['split'] == 'unused']
        
        print(f"Train data: {len(train_data)} entries")
        print(f"Valid data: {len(valid_data)} entries")
        print(f"Test data: {len(test_data)} entries")
        print(f"Unused data: {len(unused_data)} entries")
        
        # Save all split data
        print("Saving split data...")
        
        # Save valid data
        if valid_data:
            write_jsonl(valid_data, self.output_valid_path)
            print(f"Saved valid data to: {self.output_valid_path}")
        
        # Save test data
        if test_data:
            write_jsonl(test_data, self.output_test_path)
            print(f"Saved test data to: {self.output_test_path}")
        
        # Save train data with different sizes
        if train_data:
            for size in size_list:
                chunk, _ = random_token_sample(train_data, size)
                output_path = str(self.output_train_path).format(size=size // 1000)
                write_jsonl(chunk, output_path)
                print(f"Saved train data ({size//1000}k tokens) to: {output_path}")
            
            # Save full train data
            full_train_path = str(self.output_train_path).format(size="full")
            write_jsonl(train_data, full_train_path)
            print(f"Saved full train data to: {full_train_path}")
        
        # Save unused data
        if unused_data:
            unused_path = self.workspace_root / 'data_processing/code_data/split_data/L2R_unused.jsonl'
            write_jsonl(unused_data, unused_path)
            print(f"Saved unused data to: {unused_path}")
        
        print("All split data saved successfully!")
        
    
    def run_pipeline(self):
        """Run the complete processing pipeline"""
        print("🚀 Starting Data Processing Pipeline")
        print("=" * 60)
        
        try:
            # Step 1: Separate data (disabled)
            # separated_data = self.step1_separate_data()
            # Minimal change: directly wrap input as separated_data['kept_all']
            print(f"Reading input from: {self.input_path}")
            separated_data = {'kept_all': read_jsonl(self.input_path)}
            print(f"Loaded {len(separated_data['kept_all'])} entries")
            
            if not separated_data['kept_all']:
                print("⚠️ No data found. Exiting.")
                return []
            
            # Step 2: Detect leaks
            leaked_tagged_data = self.step2_detect_leaks(separated_data['kept_all'])
            # Step 3: Count tokens (disabled)
            # final_data = self.step3_count_tokens(leaked_tagged_data)
            # Step 4: Make split (disabled)
            # final_data = self.step4_make_split(final_data)
            # Step 5: Save split data (disabled)
            # self.step5_save_split_data(final_data)
            
            print("\n" + "=" * 60)
            print("✅ Leak detection completed!")
            print(f"Leaked-tagged output: {self.output_leaked_tagged_path}")
            print(f"Total processed entries: {len(leaked_tagged_data)}")
            print("=" * 60)
            
            return leaked_tagged_data
            
        except Exception as e:
            print(f"\n❌ Leak detection failed with error: {e}")
            raise

def main():
    """Main function to run the pipeline"""
    # Get the workspace root directory
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # Create and run pipeline
    pipeline = DataProcessingPipeline(workspace_root)
    pipeline.run_pipeline()

if __name__ == "__main__":
    main()
