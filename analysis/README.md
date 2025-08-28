# Data Analysis Tools

This directory contains various tools for analyzing and processing ArkTS code corpus data.

## Available Tools

### General Analysis

- **`analyze_token_distribution.py`** - Analyzes token distribution in the dataset
- **`calculate_tokens.py`** - Calculates token counts for data files
- **`show_jsonl.py`** - Utility for viewing JSONL file contents

### LLM-based Bad Case Analysis

For advanced dirty data detection and filtering using Large Language Models, see the dedicated subfolder:

- **`llm_bad_case_analysis/`** - Complete LLM-based pipeline for identifying and filtering dirty data
  - Automated bad case detection using LLMs
  - Rule generation and integration
  - Enhanced cleaning pipeline
  - See `llm_bad_case_analysis/README.md` for detailed documentation

## Usage

Each tool can be run independently. For the LLM-based analysis pipeline, navigate to the `llm_bad_case_analysis` folder for comprehensive documentation and examples.

## Requirements

General analysis tools require:
- Python 3.7+
- Standard libraries (json, argparse, etc.)

For LLM-based analysis, see `llm_bad_case_analysis/README.md` for specific requirements.