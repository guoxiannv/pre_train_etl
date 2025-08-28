# Data Processing Module

The data processing module provides comprehensive tools for extracting, cleaning, transforming, and preparing HarmonyOS ArkTS code data for language model pretraining.

## Overview

This module handles the complete data processing pipeline:
1. Code extraction from repositories
2. Data cleaning and validation
3. Format standardization and conversion
4. Data augmentation and transformation
5. Documentation processing

## Directory Structure

```
data_processing/
├── code_data/              # Code extraction and cleaning
├── docs_data/              # Documentation processing
├── preprocess/             # Advanced preprocessing
│   ├── data_augmentation/  # Data augmentation techniques
│   └── prompt_templates/   # Template files
└── README.md              # Module documentation
```

## Components

### Code Data Processing (`code_data/`)

#### `extract_ets.py`
Extracts ArkTS/ETS code files from downloaded repositories.

**Features:**
- Recursive file discovery in repository directories
- ArkTS/ETS file filtering (.ets, .ts extensions)
- Code content extraction and validation
- Metadata preservation (file paths, sizes, timestamps)
- Duplicate detection and removal

**Usage:**
```bash
python extract_ets.py
```

**Output Formats:**
- Raw extracted files: `4k_origin_file.jsonl`
- Cleaned data: `4k_file_cleaned_3k.jsonl`
- Formatted data: `arkui_2k_pretrain_cleaned.jsonl`

#### `format_starcode_data.py`
Formats code data for StarCode model training.

**Features:**
- StarCode-specific formatting
- Token optimization
- Batch processing
- Quality validation

#### `data_analysis.py`
Analyzes extracted code data for quality and statistics.

**Features:**
- Code quality metrics
- Language distribution analysis
- File size statistics
- Complexity analysis

### Documentation Processing (`docs_data/`)

#### `md_doc_processer.py`
Processes Markdown documentation files.

**Features:**
- Markdown parsing and extraction
- Code block identification
- Documentation-code linking
- Quality filtering

**Output Files:**
- `doc_inject.json/jsonl` - Processed documentation
- `pure_code.json/jsonl` - Extracted code snippets

### Advanced Preprocessing (`preprocess/`)

#### `pre_process_modified.py`
Main preprocessing pipeline with advanced features.

**Features:**
- Multi-stage data cleaning
- Code normalization
- Quality scoring
- Batch processing with progress tracking

#### Data Augmentation (`data_augmentation/`)

##### `FIM_builder.py`
Implements Fill-in-the-Middle (FIM) data augmentation.

**Features:**
- FIM sequence generation
- Configurable masking strategies
- Context preservation
- Quality validation

**Usage:**
```python
from data_augmentation.FIM_builder import FIMBuilder

builder = FIMBuilder()
fim_data = builder.build_fim_sequences(code_data)
```

##### `transformation.py`
Code transformation utilities.

**Features:**
- Syntax-aware transformations
- Code style normalization
- Comment processing
- Import statement handling

##### `variable_name_randomizer.py`
Randomizes variable names for data augmentation.

**Features:**
- Semantic-preserving variable renaming
- Scope-aware transformations
- Configurable randomization levels
- AST-based processing

#### `data_mixture.py`
Mixes different data sources for training.

**Features:**
- Multi-source data combination
- Ratio-based mixing
- Quality balancing
- Deduplication

## Data Formats

### JSONL Format
Standard format for processed data:
```json
{
  "text": "// ArkTS code content",
  "meta": {
    "file_path": "path/to/file.ets",
    "repo_name": "repository_name",
    "file_size": 1024,
    "language": "arkts",
    "quality_score": 0.85
  }
}
```

### Completion Format
For completion-style training:
```json
{
  "prompt": "// Function to calculate sum",
  "completion": "function sum(a: number, b: number): number {\n  return a + b;\n}",
  "meta": {...}
}
```

### FIM Format
For Fill-in-the-Middle training:
```json
{
  "prefix": "function calculate(",
  "middle": "a: number, b: number",
  "suffix": "): number {\n  return a + b;\n}",
  "meta": {...}
}
```

## Processing Pipeline

### Stage 1: Extraction
1. **Repository Scanning**: Discover all code files
2. **File Filtering**: Select relevant file types
3. **Content Extraction**: Read and validate file contents
4. **Metadata Collection**: Gather file and repository metadata

### Stage 2: Cleaning
1. **Syntax Validation**: Check code syntax correctness
2. **Quality Filtering**: Remove low-quality code
3. **Deduplication**: Remove duplicate content
4. **Normalization**: Standardize code formatting

### Stage 3: Transformation
1. **Format Conversion**: Convert to training formats
2. **Data Augmentation**: Apply augmentation techniques
3. **Tokenization**: Prepare for model training
4. **Quality Scoring**: Assign quality metrics

### Stage 4: Output
1. **Format Validation**: Ensure output format correctness
2. **Statistics Generation**: Create processing reports
3. **File Organization**: Organize output files
4. **Documentation**: Generate processing documentation

## Quality Control

### Code Quality Metrics
- **Syntax Correctness**: Valid ArkTS/TypeScript syntax
- **Completeness**: Complete functions and classes
- **Complexity**: Appropriate code complexity
- **Documentation**: Presence of comments and documentation

### Filtering Criteria
- Minimum file size: 100 characters
- Maximum file size: 50KB
- Syntax error tolerance: 0%
- Duplicate content: Removed

### Quality Scoring
```python
quality_score = (
    syntax_score * 0.4 +
    completeness_score * 0.3 +
    documentation_score * 0.2 +
    complexity_score * 0.1
)
```

## Configuration

### Processing Parameters
```python
CONFIG = {
    'min_file_size': 100,
    'max_file_size': 51200,
    'quality_threshold': 0.7,
    'batch_size': 1000,
    'max_workers': 4,
    'enable_augmentation': True,
    'fim_ratio': 0.3
}
```

### File Type Filters
```python
SUPPORTED_EXTENSIONS = [
    '.ets',     # ArkTS files
    '.ts',      # TypeScript files
    '.js',      # JavaScript files (if relevant)
    '.json'     # Configuration files
]
```

## Performance Optimization

### Memory Management
- Process files in batches
- Use generators for large datasets
- Clear intermediate results
- Monitor memory usage

### Processing Speed
- Parallel processing for I/O operations
- Efficient file reading strategies
- Optimized regular expressions
- Caching for repeated operations

### Storage Efficiency
- Compressed output formats
- Incremental processing
- Temporary file cleanup
- Efficient data structures

## Monitoring and Logging

### Progress Tracking
```python
from tqdm import tqdm

for file in tqdm(files, desc="Processing files"):
    process_file(file)
```

### Quality Metrics
- Files processed: Count and percentage
- Quality distribution: Histogram of quality scores
- Error rates: Syntax errors, processing failures
- Output statistics: File sizes, token counts

### Error Handling
- Graceful error recovery
- Detailed error logging
- Partial result preservation
- Retry mechanisms

## Best Practices

### Data Quality
1. **Validate Early**: Check syntax before processing
2. **Filter Aggressively**: Remove low-quality content
3. **Preserve Metadata**: Keep processing history
4. **Monitor Quality**: Track quality metrics

### Performance
1. **Batch Processing**: Process files in batches
2. **Parallel Execution**: Use multiprocessing
3. **Memory Efficiency**: Use generators and streaming
4. **Caching**: Cache expensive operations

### Reproducibility
1. **Version Control**: Track processing versions
2. **Configuration Management**: Save processing parameters
3. **Seed Management**: Use fixed seeds for randomization
4. **Documentation**: Document all processing steps

## Troubleshooting

### Common Issues

#### Memory Errors
**Problem**: Out of memory during processing
**Solution**: Reduce batch size, use streaming processing

#### Slow Processing
**Problem**: Processing takes too long
**Solution**: Increase parallelism, optimize filters

#### Quality Issues
**Problem**: Low-quality output data
**Solution**: Adjust quality thresholds, improve filters

#### Format Errors
**Problem**: Invalid output format
**Solution**: Validate output schema, check encoding

### Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Process single file for debugging
result = process_single_file("debug_file.ets")
print(f"Processing result: {result}")
```