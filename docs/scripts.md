# Scripts Module Documentation

This module contains utility scripts and automation tools for the pretrain_etl pipeline. These scripts provide convenient interfaces for common tasks and workflow automation.

## Overview

The scripts module includes:
- **Sampling Scripts**: Data sampling and subset creation tools
- **Automation Scripts**: Workflow automation and batch processing
- **Utility Scripts**: Helper tools for common operations
- **Example Scripts**: Demonstration and tutorial scripts

## Directory Structure

```
scripts/
├── run_sampling_example.py    # Example sampling script
├── sampling_script.py         # Core sampling functionality
└── README.md                   # Scripts documentation
```

## Core Scripts

### Sampling Scripts

#### `sampling_script.py`
Core sampling functionality for creating data subsets.

**Features:**
- Multiple sampling strategies (random, stratified, systematic)
- Configurable sample sizes and ratios
- Quality-based sampling
- Balanced dataset creation
- Export to various formats

**Key Functions:**
```python
def random_sampling(data, sample_size, seed=None):
    """Random sampling from dataset"""
    
def stratified_sampling(data, strata_column, sample_ratio):
    """Stratified sampling by category"""
    
def quality_based_sampling(data, quality_threshold, max_samples):
    """Sample based on quality metrics"""
    
def balanced_sampling(data, target_column, samples_per_class):
    """Create balanced samples across classes"""
```

**Usage Examples:**
```python
from sampling_script import random_sampling, stratified_sampling

# Random sampling
sample_data = random_sampling(full_dataset, sample_size=1000, seed=42)

# Stratified sampling by repository type
stratified_sample = stratified_sampling(
    data=full_dataset,
    strata_column='repo_type',
    sample_ratio=0.1
)

# Quality-based sampling
high_quality_sample = quality_based_sampling(
    data=full_dataset,
    quality_threshold=0.8,
    max_samples=5000
)
```

#### `run_sampling_example.py`
Example script demonstrating sampling workflows.

**Features:**
- Complete sampling workflow example
- Configuration templates
- Output formatting
- Performance benchmarking
- Error handling examples

**Usage:**
```bash
# Run basic sampling example
python scripts/run_sampling_example.py

# Run with custom parameters
python scripts/run_sampling_example.py --input data.jsonl --output sample.jsonl --size 1000
```

**Configuration:**
```python
sampling_config = {
    'input_file': 'data_processing/code_data/processed_data.jsonl',
    'output_file': 'sample_output.jsonl',
    'sampling_method': 'random',
    'sample_size': 1000,
    'quality_filter': True,
    'min_quality_score': 0.7,
    'seed': 42
}
```

## Sampling Strategies

### Random Sampling

**Description**: Randomly select samples from the dataset.

**Use Cases:**
- Quick dataset previews
- Unbiased sample creation
- Performance testing with smaller datasets

**Implementation:**
```python
import random
import pandas as pd

def random_sampling(data, sample_size, seed=None):
    if seed is not None:
        random.seed(seed)
    
    if isinstance(data, pd.DataFrame):
        return data.sample(n=sample_size, random_state=seed)
    elif isinstance(data, list):
        return random.sample(data, sample_size)
    else:
        raise ValueError("Unsupported data type")
```

### Stratified Sampling

**Description**: Sample proportionally from different strata/categories.

**Use Cases:**
- Maintaining category distributions
- Balanced representation
- Domain-specific sampling

**Implementation:**
```python
def stratified_sampling(data, strata_column, sample_ratio):
    if isinstance(data, pd.DataFrame):
        return data.groupby(strata_column).apply(
            lambda x: x.sample(frac=sample_ratio)
        ).reset_index(drop=True)
    else:
        raise ValueError("Stratified sampling requires DataFrame")
```

### Quality-Based Sampling

**Description**: Sample based on quality metrics and thresholds.

**Use Cases:**
- High-quality dataset creation
- Filtering low-quality samples
- Curated dataset generation

**Quality Metrics:**
- Code complexity scores
- Documentation completeness
- Syntax correctness
- Repository activity metrics

**Implementation:**
```python
def quality_based_sampling(data, quality_column, threshold, max_samples):
    # Filter by quality threshold
    high_quality = data[data[quality_column] >= threshold]
    
    # Sort by quality (descending)
    sorted_data = high_quality.sort_values(quality_column, ascending=False)
    
    # Take top samples
    return sorted_data.head(max_samples)
```

### Systematic Sampling

**Description**: Sample at regular intervals from ordered data.

**Use Cases:**
- Time-series data sampling
- Ordered dataset sampling
- Regular interval selection

**Implementation:**
```python
def systematic_sampling(data, sample_size):
    total_size = len(data)
    interval = total_size // sample_size
    
    indices = [i * interval for i in range(sample_size)]
    
    if isinstance(data, pd.DataFrame):
        return data.iloc[indices]
    elif isinstance(data, list):
        return [data[i] for i in indices]
```

## Advanced Sampling Features

### Multi-Stage Sampling

**Description**: Combine multiple sampling strategies in sequence.

```python
def multi_stage_sampling(data, stages):
    result = data
    
    for stage in stages:
        method = stage['method']
        params = stage['params']
        
        if method == 'random':
            result = random_sampling(result, **params)
        elif method == 'stratified':
            result = stratified_sampling(result, **params)
        elif method == 'quality':
            result = quality_based_sampling(result, **params)
    
    return result

# Example usage
stages = [
    {'method': 'quality', 'params': {'quality_column': 'score', 'threshold': 0.8, 'max_samples': 10000}},
    {'method': 'stratified', 'params': {'strata_column': 'language', 'sample_ratio': 0.1}},
    {'method': 'random', 'params': {'sample_size': 1000, 'seed': 42}}
]

final_sample = multi_stage_sampling(original_data, stages)
```

### Weighted Sampling

**Description**: Sample with different probabilities based on weights.

```python
def weighted_sampling(data, weight_column, sample_size):
    weights = data[weight_column].values
    weights = weights / weights.sum()  # Normalize
    
    indices = np.random.choice(
        len(data), 
        size=sample_size, 
        p=weights, 
        replace=False
    )
    
    return data.iloc[indices]
```

### Reservoir Sampling

**Description**: Sample from streaming data or very large datasets.

```python
def reservoir_sampling(data_stream, sample_size):
    reservoir = []
    
    for i, item in enumerate(data_stream):
        if i < sample_size:
            reservoir.append(item)
        else:
            # Replace with decreasing probability
            j = random.randint(0, i)
            if j < sample_size:
                reservoir[j] = item
    
    return reservoir
```

## Configuration Management

### Configuration Files

#### `sampling_config.json`
```json
{
  "default_sampling": {
    "method": "random",
    "sample_size": 1000,
    "seed": 42
  },
  "quality_sampling": {
    "method": "quality",
    "quality_threshold": 0.8,
    "max_samples": 5000,
    "quality_metrics": ["complexity", "documentation", "activity"]
  },
  "stratified_sampling": {
    "method": "stratified",
    "strata_column": "repository_type",
    "sample_ratio": 0.1,
    "min_samples_per_stratum": 10
  }
}
```

#### `output_config.json`
```json
{
  "output_formats": {
    "jsonl": {
      "extension": ".jsonl",
      "compression": "gzip",
      "encoding": "utf-8"
    },
    "csv": {
      "extension": ".csv",
      "separator": ",",
      "encoding": "utf-8"
    },
    "parquet": {
      "extension": ".parquet",
      "compression": "snappy"
    }
  },
  "metadata": {
    "include_sampling_info": true,
    "include_timestamps": true,
    "include_source_info": true
  }
}
```

### Configuration Loading

```python
import json

def load_sampling_config(config_file='sampling_config.json'):
    with open(config_file, 'r') as f:
        return json.load(f)

def apply_config(data, config_name='default_sampling'):
    config = load_sampling_config()
    sampling_params = config[config_name]
    
    method = sampling_params['method']
    
    if method == 'random':
        return random_sampling(data, **sampling_params)
    elif method == 'quality':
        return quality_based_sampling(data, **sampling_params)
    elif method == 'stratified':
        return stratified_sampling(data, **sampling_params)
```

## Output Formats

### JSONL Output

```python
def save_to_jsonl(data, output_file, metadata=None):
    with open(output_file, 'w', encoding='utf-8') as f:
        if metadata:
            f.write(json.dumps({"_metadata": metadata}) + '\n')
        
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
```

### CSV Output

```python
def save_to_csv(data, output_file, include_metadata=True):
    if isinstance(data, pd.DataFrame):
        data.to_csv(output_file, index=False, encoding='utf-8')
    else:
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
```

### Parquet Output

```python
def save_to_parquet(data, output_file, compression='snappy'):
    if isinstance(data, pd.DataFrame):
        data.to_parquet(output_file, compression=compression)
    else:
        df = pd.DataFrame(data)
        df.to_parquet(output_file, compression=compression)
```

## Performance Optimization

### Memory Management

```python
def memory_efficient_sampling(input_file, output_file, sample_size):
    """Sample large files without loading everything into memory"""
    
    # First pass: count total lines
    total_lines = sum(1 for _ in open(input_file, 'r'))
    
    # Calculate sampling probability
    sample_prob = sample_size / total_lines
    
    # Second pass: sample lines
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if random.random() < sample_prob:
                outfile.write(line)
```

### Parallel Processing

```python
from multiprocessing import Pool
import functools

def parallel_sampling(data_chunks, sampling_func, **kwargs):
    """Apply sampling function to data chunks in parallel"""
    
    partial_func = functools.partial(sampling_func, **kwargs)
    
    with Pool() as pool:
        results = pool.map(partial_func, data_chunks)
    
    # Combine results
    return pd.concat(results, ignore_index=True)
```

### Streaming Processing

```python
def streaming_sampling(input_stream, sample_size, chunk_size=1000):
    """Sample from streaming data in chunks"""
    
    reservoir = []
    processed = 0
    
    while True:
        chunk = list(itertools.islice(input_stream, chunk_size))
        if not chunk:
            break
        
        for item in chunk:
            if len(reservoir) < sample_size:
                reservoir.append(item)
            else:
                # Reservoir sampling logic
                j = random.randint(0, processed)
                if j < sample_size:
                    reservoir[j] = item
            processed += 1
    
    return reservoir
```

## Quality Metrics

### Code Quality Metrics

```python
def calculate_code_quality(code_content):
    """Calculate various code quality metrics"""
    
    metrics = {
        'lines_of_code': len(code_content.split('\n')),
        'complexity_score': calculate_complexity(code_content),
        'documentation_ratio': calculate_doc_ratio(code_content),
        'syntax_correctness': check_syntax(code_content)
    }
    
    # Composite quality score
    metrics['quality_score'] = (
        metrics['complexity_score'] * 0.3 +
        metrics['documentation_ratio'] * 0.3 +
        metrics['syntax_correctness'] * 0.4
    )
    
    return metrics
```

### Repository Quality Metrics

```python
def calculate_repo_quality(repo_metadata):
    """Calculate repository-level quality metrics"""
    
    metrics = {
        'activity_score': calculate_activity_score(repo_metadata),
        'popularity_score': calculate_popularity_score(repo_metadata),
        'maintenance_score': calculate_maintenance_score(repo_metadata),
        'documentation_score': calculate_doc_score(repo_metadata)
    }
    
    # Weighted composite score
    weights = {'activity': 0.25, 'popularity': 0.25, 'maintenance': 0.25, 'documentation': 0.25}
    
    metrics['overall_quality'] = sum(
        metrics[f'{key}_score'] * weight 
        for key, weight in weights.items()
    )
    
    return metrics
```

## Monitoring and Logging

### Progress Tracking

```python
from tqdm import tqdm
import logging

def sampling_with_progress(data, sampling_func, **kwargs):
    """Apply sampling with progress tracking"""
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting sampling with {len(data)} items")
    
    # Add progress bar
    with tqdm(total=len(data), desc="Sampling") as pbar:
        result = sampling_func(data, **kwargs)
        pbar.update(len(data))
    
    logger.info(f"Sampling completed. Result size: {len(result)}")
    return result
```

### Performance Metrics

```python
import time
import psutil

def measure_sampling_performance(sampling_func, data, **kwargs):
    """Measure sampling performance metrics"""
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    result = sampling_func(data, **kwargs)
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss
    
    metrics = {
        'execution_time': end_time - start_time,
        'memory_used': end_memory - start_memory,
        'input_size': len(data),
        'output_size': len(result),
        'sampling_ratio': len(result) / len(data),
        'throughput': len(data) / (end_time - start_time)
    }
    
    return result, metrics
```

## Best Practices

### Sampling Guidelines

1. **Reproducibility**: Always use seeds for random sampling
2. **Validation**: Validate sample representativeness
3. **Documentation**: Document sampling methodology
4. **Quality Control**: Implement quality checks
5. **Performance**: Optimize for large datasets

### Code Quality

1. **Error Handling**: Implement comprehensive error handling
2. **Type Hints**: Use type hints for better code clarity
3. **Testing**: Write unit tests for sampling functions
4. **Documentation**: Provide clear function documentation
5. **Modularity**: Keep functions focused and reusable

### Data Integrity

1. **Backup**: Backup original data before sampling
2. **Validation**: Validate sample integrity
3. **Metadata**: Preserve important metadata
4. **Traceability**: Maintain sampling audit trails
5. **Verification**: Verify sample quality

## Common Use Cases

### Development Dataset Creation

```python
# Create small development dataset
dev_sample = random_sampling(
    data=full_dataset,
    sample_size=1000,
    seed=42
)

save_to_jsonl(dev_sample, 'dev_dataset.jsonl')
```

### Model Training Subsets

```python
# Create balanced training subset
training_sample = stratified_sampling(
    data=full_dataset,
    strata_column='complexity_level',
    sample_ratio=0.1
)

save_to_parquet(training_sample, 'training_subset.parquet')
```

### Quality Evaluation Sets

```python
# Create high-quality evaluation set
eval_sample = quality_based_sampling(
    data=full_dataset,
    quality_column='quality_score',
    threshold=0.9,
    max_samples=500
)

save_to_csv(eval_sample, 'evaluation_set.csv')
```

### Performance Testing

```python
# Create performance test dataset
perf_sample = systematic_sampling(
    data=full_dataset,
    sample_size=100
)

save_to_jsonl(perf_sample, 'performance_test.jsonl')
```

## Troubleshooting

### Common Issues

#### Memory Errors
**Problem**: Out of memory when sampling large datasets
**Solution**: Use streaming or chunk-based sampling

#### Sampling Bias
**Problem**: Sample not representative of population
**Solution**: Use stratified sampling or validate representativeness

#### Performance Issues
**Problem**: Slow sampling on large datasets
**Solution**: Use parallel processing or optimized algorithms

#### Quality Issues
**Problem**: Low-quality samples in output
**Solution**: Implement quality filters and validation

### Debugging Tips

1. **Logging**: Enable detailed logging for debugging
2. **Profiling**: Profile code to identify bottlenecks
3. **Validation**: Validate inputs and outputs
4. **Testing**: Test with small datasets first
5. **Monitoring**: Monitor resource usage during sampling