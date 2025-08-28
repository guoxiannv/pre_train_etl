#!/usr/bin/env python3
"""
Hugging Face Model Download Script

This script downloads Hugging Face models to a specified directory.
Supports both models and datasets with various configuration options.
"""

import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any

from huggingface_hub import login, snapshot_download, hf_hub_download
from datasets import load_dataset


def setup_proxy():
    """Setup proxy configuration if needed"""
    proxy_url = "http://127.0.0.1:10809"
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    print(f"Proxy configured: {proxy_url}")


def authenticate_hf(token: Optional[str] = None):
    """Authenticate with Hugging Face Hub"""
    if token:
        login(token=token)
        print("Authenticated with provided token")
    else:
        # Try to use existing token or prompt for login
        try:
            login()
            print("Authenticated with existing token")
        except Exception as e:
            print(f"Authentication failed: {e}")
            print("Please provide a valid HF token or run 'huggingface-cli login'")
            return False
    return True


def download_model(model_name: str, 
                  download_dir: str,
                  revision: str = "main",
                  cache_dir: Optional[str] = None,
                  force_download: bool = False,
                  resume_download: bool = True) -> str:
    """Download a Hugging Face model to specified directory"""
    
    print(f"Downloading model: {model_name}")
    print(f"Target directory: {download_dir}")
    print(f"Revision: {revision}")
    
    try:
        # Create download directory if it doesn't exist
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        
        # Download the model
        downloaded_path = snapshot_download(
            repo_id=model_name,
            local_dir=download_dir,
            revision=revision,
            cache_dir=cache_dir,
            force_download=force_download,
            resume_download=resume_download,
            local_dir_use_symlinks=False  # Use actual files instead of symlinks
        )
        
        print(f"Model downloaded successfully to: {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        raise


def download_dataset(dataset_name: str,
                    download_dir: str,
                    config_name: Optional[str] = None,
                    split: Optional[str] = None,
                    data_dir: Optional[str] = None,
                    streaming: bool = False,
                    save_format: str = "jsonl") -> str:
    """Download a Hugging Face dataset to specified directory"""
    
    print(f"Downloading dataset: {dataset_name}")
    print(f"Target directory: {download_dir}")
    
    try:
        # Create download directory if it doesn't exist
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        
        # Load the dataset
        dataset = load_dataset(
            dataset_name,
            name=config_name,
            data_dir=data_dir,
            split=split,
            streaming=streaming,
            cache_dir=download_dir
        )
        
        # Save dataset in specified format
        if not streaming:
            output_file = Path(download_dir) / f"{dataset_name.replace('/', '_')}.{save_format}"
            
            if save_format == "jsonl":
                with open(output_file, "w", encoding="utf-8") as f:
                    for example in dataset:
                        f.write(json.dumps(example, ensure_ascii=False) + "\n")
            elif save_format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(list(dataset), f, ensure_ascii=False, indent=2)
            
            print(f"Dataset saved to: {output_file}")
            print(f"Number of examples: {len(dataset)}")
        else:
            print("Streaming dataset loaded. Use the returned dataset object to process data.")
        
        return str(download_dir)
        
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Download Hugging Face models or datasets to a specific directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a model
  python download_hf_model.py --type model --name microsoft/DialoGPT-medium --dir ./models/dialogpt
  
  # Download a dataset
  python download_hf_model.py --type dataset --name squad --dir ./datasets/squad
  
  # Download with authentication token
  python download_hf_model.py --type model --name meta-llama/Llama-2-7b-hf --dir ./models/llama2 --token YOUR_TOKEN
  
  # Download specific dataset split
  python download_hf_model.py --type dataset --name bigcode/starcoderdata --dir ./datasets/starcode --config python --split train
        """
    )
    
    parser.add_argument("--type", choices=["model", "dataset"], required=True,
                       help="Type of content to download")
    parser.add_argument("--name", required=True,
                       help="Name of the model or dataset (e.g., 'microsoft/DialoGPT-medium')")
    parser.add_argument("--dir", required=True,
                       help="Directory to download the content to")
    parser.add_argument("--token", 
                       help="Hugging Face authentication token")
    parser.add_argument("--revision", default="main",
                       help="Model revision/branch to download (default: main)")
    parser.add_argument("--config", 
                       help="Dataset configuration name")
    parser.add_argument("--split", 
                       help="Dataset split to download (e.g., 'train', 'test')")
    parser.add_argument("--data-dir", 
                       help="Dataset data directory")
    parser.add_argument("--cache-dir", 
                       help="Cache directory for downloads")
    parser.add_argument("--format", choices=["json", "jsonl"], default="jsonl",
                       help="Output format for datasets (default: jsonl)")
    parser.add_argument("--streaming", action="store_true",
                       help="Use streaming for large datasets")
    parser.add_argument("--force-download", action="store_true",
                       help="Force re-download even if files exist")
    parser.add_argument("--no-proxy", action="store_true",
                       help="Disable proxy configuration")
    
    args = parser.parse_args()
    
    # Setup proxy if not disabled
    if not args.no_proxy:
        setup_proxy()
    
    # Authenticate
    if not authenticate_hf(args.token):
        return 1
    
    try:
        if args.type == "model":
            download_model(
                model_name=args.name,
                download_dir=args.dir,
                revision=args.revision,
                cache_dir=args.cache_dir,
                force_download=args.force_download
            )
        elif args.type == "dataset":
            download_dataset(
                dataset_name=args.name,
                download_dir=args.dir,
                config_name=args.config,
                split=args.split,
                data_dir=args.data_dir,
                streaming=args.streaming,
                save_format=args.format
            )
        
        print("\nDownload completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())