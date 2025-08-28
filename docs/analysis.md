# Analysis Module

The analysis module provides comprehensive tools for analyzing, visualizing, and understanding the collected and processed HarmonyOS ArkTS code data.

## Overview

This module offers statistical analysis and visualization capabilities for:
1. Token distribution analysis
2. Code quality metrics
3. Dataset statistics and insights
4. Data visualization and reporting

## Components

### Token Analysis

#### `analyze_token_distribution.py`
Analyzes token distribution patterns in the processed code data.

**Features:**
- Token frequency analysis
- Distribution visualization
- Statistical summaries
- Language-specific token patterns
- Vocabulary analysis

**Key Metrics:**
- Total token count
- Unique token count
- Token frequency distribution
- Average tokens per file
- Token diversity metrics

**Usage:**
```bash
python analyze_token_distribution.py
```

**Output:**
- Token distribution histograms
- Statistical summary reports
- Vocabulary frequency tables
- Distribution plots and charts

#### `calculate_tokens.py`
Calculates detailed token statistics for datasets.

**Features:**
- Precise token counting
- Multiple tokenization methods
- Batch processing capabilities
- Memory-efficient processing
- Export to various formats

**Supported Tokenizers:**
- GPT-style tokenizers
- SentencePiece tokenizers
- Custom ArkTS tokenizers
- Whitespace tokenizers

**Usage:**
```bash
# Basic token calculation
python calculate_tokens.py --input data.jsonl

# With specific tokenizer
python calculate_tokens.py --input data.jsonl --tokenizer gpt2

# Batch processing
python calculate_tokens.py --input-dir ./datasets/
```

**Output Formats:**
- JSON statistics files
- CSV summary tables
- Text reports
- Visualization plots

### Data Visualization

#### `show_jsonl.py`
Interactive data viewer and explorer for JSONL datasets.

**Features:**
- Interactive data browsing
- Sample data display
- Quick statistics overview
- Search and filtering
- Export capabilities

**Usage:**
```bash
# View dataset
python show_jsonl.py dataset.jsonl

# With filtering
python show_jsonl.py dataset.jsonl --filter "quality_score > 0.8"

# Show specific fields
python show_jsonl.py dataset.jsonl --fields text,meta.quality_score
```

**Interactive Features:**
- Pagination through large datasets
- Real-time search
- Field-specific filtering
- Export filtered results

## Analysis Types

### Statistical Analysis

#### Basic Statistics
```python
stats = {
    'total_files': 10000,
    'total_tokens': 5000000,
    'avg_tokens_per_file': 500,
    'median_tokens_per_file': 350,
    'std_tokens_per_file': 200
}
```

#### Distribution Analysis
- **Token Length Distribution**: Histogram of token counts per file
- **Quality Score Distribution**: Distribution of quality metrics
- **File Size Distribution**: Analysis of file sizes
- **Language Feature Distribution**: Usage of specific language features

#### Correlation Analysis
- Quality vs. file size correlation
- Token count vs. complexity correlation
- Repository popularity vs. code quality

### Quality Metrics

#### Code Quality Indicators
```python
quality_metrics = {
    'syntax_correctness': 0.95,    # Percentage of syntactically correct files
    'completeness_score': 0.87,    # Average completeness score
    'documentation_ratio': 0.65,   # Files with documentation
    'complexity_score': 0.72,      # Average complexity score
    'duplication_rate': 0.03       # Percentage of duplicate content
}
```

#### Data Quality Assessment
- **Completeness**: Percentage of complete code structures
- **Correctness**: Syntax and semantic correctness
- **Consistency**: Code style and formatting consistency
- **Coverage**: Feature and pattern coverage

### Vocabulary Analysis

#### Token Frequency Analysis
```python
top_tokens = {
    'function': 15000,
    'const': 12000,
    'let': 10000,
    'interface': 8000,
    'class': 6000
}
```

#### Language Feature Usage
- ArkTS-specific features
- TypeScript features
- Common patterns and idioms
- API usage patterns

## Visualization Capabilities

### Charts and Plots

#### Distribution Plots
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Token distribution histogram
plt.figure(figsize=(10, 6))
plt.hist(token_counts, bins=50, alpha=0.7)
plt.xlabel('Token Count')
plt.ylabel('Frequency')
plt.title('Token Distribution')
plt.show()
```

#### Quality Metrics Dashboard
```python
# Quality metrics radar chart
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False)
ax.plot(angles, values)
ax.fill(angles, values, alpha=0.25)
```

#### Correlation Heatmaps
```python
# Correlation matrix
corr_matrix = df.corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
plt.title('Feature Correlation Matrix')
```

### Interactive Visualizations

#### Plotly Dashboards
```python
import plotly.graph_objects as go
import plotly.express as px

# Interactive scatter plot
fig = px.scatter(df, x='file_size', y='quality_score', 
                 color='repo_type', hover_data=['repo_name'])
fig.show()
```

#### Streamlit Applications
```python
import streamlit as st

st.title('Code Analysis Dashboard')
st.plotly_chart(token_distribution_plot)
st.dataframe(summary_stats)
```

## Reporting

### Automated Reports

#### Summary Report Generation
```python
def generate_summary_report(dataset_path):
    report = {
        'dataset_info': get_dataset_info(dataset_path),
        'token_statistics': calculate_token_stats(dataset_path),
        'quality_metrics': assess_quality(dataset_path),
        'recommendations': generate_recommendations(dataset_path)
    }
    return report
```

#### Report Templates
- **Executive Summary**: High-level overview
- **Technical Report**: Detailed analysis
- **Quality Assessment**: Quality-focused analysis
- **Comparison Report**: Multi-dataset comparison

### Export Formats

#### Supported Formats
- **PDF Reports**: Professional formatted reports
- **HTML Dashboards**: Interactive web reports
- **JSON Data**: Machine-readable results
- **CSV Tables**: Spreadsheet-compatible data
- **Markdown**: Documentation-friendly format

## Performance Monitoring

### Processing Metrics

#### Performance Indicators
```python
performance_metrics = {
    'processing_speed': '1000 files/minute',
    'memory_usage': '2.5 GB peak',
    'disk_io': '50 MB/s average',
    'cpu_utilization': '75% average'
}
```

#### Bottleneck Analysis
- I/O bound operations identification
- Memory usage patterns
- CPU utilization analysis
- Processing time breakdown

### Scalability Analysis

#### Dataset Size Impact
```python
# Performance vs dataset size
sizes = [1000, 5000, 10000, 50000, 100000]
times = [10, 45, 90, 450, 900]  # seconds

plt.plot(sizes, times)
plt.xlabel('Dataset Size (files)')
plt.ylabel('Processing Time (seconds)')
plt.title('Scalability Analysis')
```

## Configuration

### Analysis Parameters
```python
ANALYSIS_CONFIG = {
    'tokenizer': 'gpt2',
    'max_sequence_length': 2048,
    'quality_threshold': 0.7,
    'sample_size': 10000,
    'visualization_dpi': 300,
    'export_format': 'pdf'
}
```

### Visualization Settings
```python
VIZ_CONFIG = {
    'figure_size': (12, 8),
    'color_palette': 'viridis',
    'font_size': 12,
    'save_format': 'png',
    'interactive': True
}
```

## Best Practices

### Analysis Workflow
1. **Data Validation**: Verify data integrity before analysis
2. **Sampling Strategy**: Use representative samples for large datasets
3. **Statistical Significance**: Ensure sufficient sample sizes
4. **Visualization Clarity**: Create clear, interpretable visualizations

### Performance Optimization
1. **Batch Processing**: Process data in manageable chunks
2. **Memory Management**: Use generators for large datasets
3. **Caching**: Cache expensive computations
4. **Parallel Processing**: Utilize multiple cores when possible

### Quality Assurance
1. **Cross-Validation**: Validate results across different samples
2. **Reproducibility**: Use fixed seeds for random operations
3. **Documentation**: Document analysis methodology
4. **Version Control**: Track analysis versions and parameters

## Common Use Cases

### Dataset Quality Assessment
```python
# Assess overall dataset quality
quality_report = assess_dataset_quality('dataset.jsonl')
print(f"Overall quality score: {quality_report['overall_score']}")
print(f"Recommendations: {quality_report['recommendations']}")
```

### Model Training Preparation
```python
# Analyze data for model training
training_analysis = analyze_for_training('dataset.jsonl')
print(f"Recommended batch size: {training_analysis['batch_size']}")
print(f"Estimated training time: {training_analysis['training_time']}")
```

### Comparative Analysis
```python
# Compare multiple datasets
comparison = compare_datasets(['dataset1.jsonl', 'dataset2.jsonl'])
visualize_comparison(comparison)
```

## Troubleshooting

### Common Issues

#### Memory Errors
**Problem**: Out of memory during analysis
**Solution**: Use sampling or batch processing

#### Slow Processing
**Problem**: Analysis takes too long
**Solution**: Optimize algorithms, use parallel processing

#### Visualization Errors
**Problem**: Plots not displaying correctly
**Solution**: Check dependencies, update libraries

### Debugging Tips
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Profile performance
import cProfile
cProfile.run('analyze_dataset("data.jsonl")')

# Memory profiling
from memory_profiler import profile

@profile
def analyze_memory_usage():
    # Analysis code here
    pass
```