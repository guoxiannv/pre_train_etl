# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
This is a pretraining data collection and processing pipeline for ArkTS/TypeScript code. The repository focuses on gathering, cleaning, and transforming code samples and documentation for machine learning model training.

## Project Structure

The repository is organized into the following modules:

```
pretrain_etl/
├── data_collection/          # Repository discovery, downloading, and repair
├── data_processing/          # Code and documentation processing pipelines
├── analysis/                 # Data analysis and visualization tools
├── scripts/                  # Utility scripts and automation tools
├── docs/                     # Documentation and guides
└── README.md                 # Main project documentation
```

## Key Architecture

### Data Flow
1. **Collection**: Repository discovery and downloading (`data_collection/`)
   - `download_repo.py`, `get_repo.py` - Repository downloading
   - `fix_incomplete_repos.py` - Repository repair tools
   - `download_hf_model.py` - Hugging Face model/dataset downloads

2. **Processing**: Data cleaning and transformation (`data_processing/`)
   - `preprocess/` - Code preprocessing and cleaning
   - `code_data/` - Code data processing pipeline
   - `docs_data/` - Documentation processing pipeline

3. **Analysis**: Data analysis and metrics (`analysis/`)
   - `calculate_tokens.py` - Token counting and analysis
   - `analyze_token_distribution.py` - Distribution analysis
   - `show_jsonl.py` - Data visualization tools

4. **Scripts**: Automation and utilities (`scripts/`)
   - `sampling_script.py` - Data sampling tools
   - `run_sampling_example.py` - Sampling examples

### Core Components
- **ArkTS Repository List**: `data_collection/arkts_repos.json` contains GitHub repositories
- **Code Data Pipeline**: Located in `data_processing/code_data/`
- **Documentation Pipeline**: Located in `data_processing/docs_data/`
- **Repair Tools**: Repository integrity and repair in `data_collection/`

## Common Commands

### Data Collection
```bash
# Download ArkTS repositories
python data_collection/download_repo.py

# Download Hugging Face models/datasets
python data_collection/download_hf_model.py --type model --name Qwen/Qwen2.5-Coder-3B --dir ./models/qwen

# Fix incomplete repository downloads
python data_collection/run_fix_repos.py
```

### Data Processing
```bash
# Process raw code data
python data_processing/code_data/pre_process.py

# Process documentation
python data_processing/docs_data/md_doc_processer.py --root_dir /path/to/docs --project_name myproject

# Generate FIM data
python data_processing/preprocess/data_augmentation/FIM_builder.py
```

### Data Analysis
```bash
# Calculate tokens in dataset
python analysis/calculate_tokens.py

# Analyze token distribution
python analysis/analyze_token_distribution.py

# View JSONL data
python analysis/show_jsonl.py
```

### Utility Scripts
```bash
# Run data sampling
python scripts/run_sampling_example.py

# Custom sampling
python scripts/sampling_script.py --sample_size 1000
```

## Documentation

Detailed documentation for each module:

- **[Data Collection](data_collection.md)**: Repository downloading, model downloads, and repair tools
- **[Data Processing](data_processing.md)**: Code and documentation processing pipelines
- **[Repository Repair](repository_repair.md)**: Tools for fixing incomplete repository downloads
- **[Analysis](analysis.md)**: Data analysis and visualization tools
- **[Scripts](scripts.md)**: Utility scripts and automation tools

## Quick Start

1. **Setup**: Install dependencies and configure environment
2. **Collect**: Download repositories and models using `data_collection/`
3. **Process**: Clean and transform data using `data_processing/`
4. **Analyze**: Generate metrics and insights using `analysis/`
5. **Sample**: Create training subsets using `scripts/`

## Best Practices

- Use the modular structure to organize related functionality
- Check documentation in `docs/` for detailed usage instructions
- Run repair tools after repository downloads to ensure data integrity
- Use sampling scripts to create manageable dataset subsets for development
- Monitor processing pipelines with analysis tools

## File Formats
- **JSONL**: Primary format for processed data (one JSON object per line)
- **JSON**: Used for configuration and intermediate processing
- Raw data stored in `data_processing/code_data/raw_data/` and `data_processing/code_data/cleaned_data/`

## Key Processing Features
- **SimHash filtering**: Remove duplicate/similar code samples
- **Line count filtering**: Remove files with <3 or >150 lines
- **Comment removal**: Clean code by removing comments and copyright headers
- **Language filtering**: Focus on ArkTS/TypeScript/JavaScript
- **FIM generation**: Create fill-in-the-middle training samples

## Dependencies
- `transformers`: For token counting with Qwen2.5-Coder-7B
- `tree-sitter`: For AST parsing in FIM generation
- `tqdm`: Progress bars for long operations
- Standard Python libraries: json, re, os, pathlib

## Data Visualization
```bash
# View JSONL data with Streamlit
streamlit run analysis/show_jsonl.py --server.port 6056
```

## Dataset Statistics
- TypeScript (StarCode): 404,107,043 tokens
- ArkTS repositories: 2,291 repositories processed
- Processing pipeline supports multiple data formats and quality filters