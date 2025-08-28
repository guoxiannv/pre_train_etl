# HarmonyOS ArkTS Pretraining ETL Pipeline

A comprehensive ETL (Extract, Transform, Load) pipeline for collecting, processing, and preparing HarmonyOS ArkTS code data for language model pretraining.

## Project Structure

```
pretrain_etl/
├── data_collection/          # Data collection and repository management
├── data_processing/          # Data processing and preprocessing
├── analysis/                 # Data analysis and statistics tools
├── scripts/                  # Utility and execution scripts
├── docs/                     # Documentation
├── utils.py                  # Common utilities
├── bad.ets                   # Sample problematic code
└── README.md                 # This file
```

## Modules Overview

### 📥 Data Collection (`data_collection/`)
Tools for collecting HarmonyOS repositories and managing downloads:
- Repository discovery and metadata collection
- Batch downloading with progress tracking
- Failed download recovery and repair
- Model downloading utilities

### 🔄 Data Processing (`data_processing/`)
Data preprocessing and transformation pipeline:
- Code extraction and cleaning
- Data augmentation and transformation
- Format conversion and standardization
- Documentation processing

### 📊 Analysis (`analysis/`)
Data analysis and quality assessment tools:
- Token distribution analysis
- Code statistics and metrics
- Data visualization utilities

### 🚀 Scripts (`scripts/`)
Ready-to-use execution scripts:
- Sampling and testing scripts
- Batch processing utilities

## Quick Start

### 1. Repository Collection
```bash
# Discover and collect repository metadata
cd data_collection
python get_repo.py

# Download repositories
python download_repo.py

# Fix incomplete downloads
python run_fix_repos.py
```

### 2. Data Processing
```bash
# Extract and clean code data
cd data_processing
python code_data/extract_ets.py

# Apply preprocessing
python preprocess/pre_process_modified.py
```

### 3. Analysis
```bash
# Analyze token distribution
cd analysis
python analyze_token_distribution.py

# Calculate statistics
python calculate_tokens.py
```

## Key Features

- **🔍 Smart Repository Discovery**: Automated discovery of HarmonyOS/ArkTS repositories
- **⚡ Parallel Processing**: Multi-threaded downloading and processing
- **🛠️ Error Recovery**: Automatic retry and repair mechanisms
- **📈 Progress Tracking**: Real-time progress bars and detailed logging
- **🎯 Quality Control**: Data validation and cleaning pipelines
- **📊 Analytics**: Comprehensive data analysis and visualization

## Requirements

- Python 3.8+
- Git
- Required Python packages (see individual module requirements)

## Documentation

Detailed documentation for each module can be found in the `docs/` directory:

- [Data Collection Guide](docs/data_collection.md)
- [Data Processing Guide](docs/data_processing.md)
- [Analysis Tools Guide](docs/analysis.md)
- [Repository Repair Guide](docs/repository_repair.md)

## Contributing

Contributions are welcome! Please read the contributing guidelines in the docs directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.