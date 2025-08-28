# LLM-based Bad Case Analysis Pipeline

This module provides an automated pipeline for analyzing and filtering dirty data from ArkTS code corpus using Large Language Models (LLMs). The pipeline can identify bad cases, generate filtering rules, and integrate them into the existing cleaning workflow.

## Overview

The pipeline consists of three main components:

1. **LLM Bad Case Analyzer** (`llm_bad_case_analyzer.py`) - Samples data and uses LLM to identify dirty data
2. **Rule Integrator** (`rule_integrator.py`) - Converts LLM-generated rules into executable filter functions
3. **Complete Pipeline** (`bad_case_pipeline.py`) - Orchestrates the entire workflow

## Features

- **Intelligent Sampling**: Randomly samples data for analysis to manage costs
- **LLM-powered Analysis**: Uses advanced language models to identify various types of dirty data
- **Automatic Rule Generation**: Generates filtering rules based on identified bad cases
- **Seamless Integration**: Integrates with existing heuristic filtering pipeline
- **Comprehensive Logging**: Tracks all steps and provides detailed reports
- **Customizable Prompts**: Allows customization of analysis prompts

## Installation

Ensure you have the required dependencies:

```bash
pip install openai datasketch tree-sitter tree-sitter-typescript tqdm
```

Set up your LLM API key:

```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

## Quick Start

### 1. Run Complete Pipeline

The easiest way to use the pipeline is with the complete workflow:

```bash
python analysis/bad_case_pipeline.py data.jsonl cleaned_data.jsonl --rounds 2 --sample-size 100
```

This will:
- Run 2 analysis rounds with 100 samples each
- Generate filtering rules based on identified bad cases
- Apply both existing and LLM-generated filters
- Save the cleaned data to `cleaned_data.jsonl`

### 2. Analysis Only

To only run the bad case analysis without applying filters:

```bash
python analysis/llm_bad_case_analyzer.py data.jsonl --sample-size 100 --batch-name my_analysis
```

### 3. Rule Integration Only

To integrate previously generated rules:

```bash
python analysis/rule_integrator.py analysis_results/my_analysis_report.json data.jsonl filtered_data.jsonl
```

## Detailed Usage

### LLM Bad Case Analyzer

```python
from analysis.llm_bad_case_analyzer import LLMBadCaseAnalyzer
from utils import read_jsonl

# Initialize analyzer
analyzer = LLMBadCaseAnalyzer(
    model="qwen3-coder-plus",
    temperature=0.3,
    output_dir="./analysis_results"
)

# Load and analyze data
data = read_jsonl("your_data.jsonl")
samples = analyzer.sample_data(data, sample_size=100)
report = analyzer.analyze_batch(samples, batch_name="round_1")

print(f"Found {report.dirty_count} dirty samples out of {report.total_samples}")
```

### Rule Integrator

```python
from analysis.rule_integrator import RuleIntegrator

# Initialize integrator
integrator = RuleIntegrator(rules_dir="./analysis_results")

# Load rules from analysis report
rules = integrator.load_rules_from_analysis("analysis_results/round_1_report.json")

# Convert and register filters
for rule in rules:
    filter_func = integrator.convert_rule_to_filter(rule)
    if filter_func:
        rule_name = rule['name'].lower().replace(' ', '_')
        integrator.register_custom_filter(rule_name, filter_func)

# Apply filters
filtered_data = integrator.apply_custom_filters(data)
```

### Complete Pipeline

```python
from analysis.bad_case_pipeline import BadCasePipeline

# Initialize pipeline
pipeline = BadCasePipeline(
    output_dir="./pipeline_results",
    model="qwen3-coder-plus",
    temperature=0.3
)

# Run complete workflow
results = pipeline.run_complete_pipeline(
    data_file="raw_data.jsonl",
    output_file="cleaned_data.jsonl",
    num_rounds=2,
    sample_size=100,
    use_existing_pipeline=True
)

# Print summary
pipeline.print_summary(results)
```

## Configuration

### LLM Settings

- **Model**: Default is `qwen3-coder-plus`, but you can use any OpenAI-compatible model
- **Temperature**: Controls randomness (0.0-1.0). Lower values are more deterministic
- **API Key**: Set via `DASHSCOPE_API_KEY` environment variable

### Analysis Parameters

- **Sample Size**: Number of samples to analyze per round (default: 100)
- **Number of Rounds**: Multiple rounds can capture different types of bad cases
- **Output Directory**: Where to save analysis results and logs

### Filter Categories

The pipeline can identify and filter:

1. **Auto-generated Code**: Boilerplate, scaffolding, generated files
2. **Test Code**: Unit tests, test files with minimal logic
3. **Configuration Files**: JSON configs, settings files
4. **Incomplete Code**: Broken, partial, or malformed code
5. **Excessive Comments**: Files with too many comments vs. code
6. **Trivial Code**: Hello-world examples, minimal logic
7. **Poor Formatting**: Badly structured or formatted code
8. **Meaningless Variables**: Code with non-descriptive variable names
9. **Import-heavy Files**: Files that are mostly import statements
10. **Duplicated Code**: Repetitive or template code

## Output Files

### Analysis Results

- `{batch_name}_report.json`: Analysis summary with statistics and generated rules
- `{batch_name}_bad_cases.jsonl`: Detailed bad case examples with classifications

### Integration Results

- `integration_report.json`: Filter registration and application statistics
- `removed_{filter_name}_filter.jsonl`: Records removed by each filter

### Pipeline Results

- `pipeline_final_report.json`: Complete pipeline execution summary
- `existing_filter_logs/`: Logs from existing heuristic filters
- `analysis/`: All analysis results and generated rules

## Customization

### Custom Prompts

You can customize the analysis prompts:

```python
analyzer = LLMBadCaseAnalyzer()

# Custom detection prompt
analyzer.detection_prompt = """
Your custom prompt for detecting dirty data...
Code to analyze:
```
{code}
```
"""

# Custom rule generation prompt
analyzer.rule_generation_prompt = """
Your custom prompt for generating rules...
Bad cases: {bad_cases_summary}
"""
```

### Custom Filters

You can add custom filter functions:

```python
def my_custom_filter(text: str) -> bool:
    """Custom filter logic"""
    # Return True to keep, False to filter out
    return len(text) > 100

integrator.register_custom_filter("my_filter", my_custom_filter)
```

## Best Practices

1. **Start Small**: Begin with smaller sample sizes (50-100) to test the pipeline
2. **Multiple Rounds**: Run multiple analysis rounds to capture diverse bad cases
3. **Review Results**: Always review the generated rules and bad cases before applying to full dataset
4. **Iterative Improvement**: Use the pipeline iteratively to continuously improve data quality
5. **Cost Management**: Monitor LLM API usage, especially with large sample sizes

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `DASHSCOPE_API_KEY` is set correctly
2. **JSON Parse Error**: LLM responses might not always be valid JSON. The pipeline handles this gracefully
3. **Memory Issues**: For large datasets, consider processing in smaller batches
4. **Rate Limiting**: If you hit API rate limits, reduce sample size or add delays

### Performance Tips

1. Use appropriate sample sizes based on your data size and budget
2. Set temperature to 0.1-0.3 for more consistent results
3. Cache analysis results to avoid re-analyzing the same data
4. Use the existing heuristic pipeline first to reduce LLM analysis load

## Examples

### Example 1: Basic Analysis

```bash
# Analyze 50 samples and generate rules
python analysis/llm_bad_case_analyzer.py data/raw_data.jsonl --sample-size 50
```

### Example 2: Multi-round Pipeline

```bash
# Run 3 rounds of analysis with 100 samples each
python analysis/bad_case_pipeline.py data/raw_data.jsonl data/cleaned_data.jsonl \
    --rounds 3 --sample-size 100 --output-dir results/
```

### Example 3: Integration Only

```bash
# Apply previously generated rules to new data
python analysis/rule_integrator.py results/analysis/round_1_report.json \
    data/new_data.jsonl data/filtered_new_data.jsonl
```

## API Reference

See the docstrings in each module for detailed API documentation:

- `LLMBadCaseAnalyzer`: Main analysis class
- `RuleIntegrator`: Rule conversion and application
- `BadCasePipeline`: Complete workflow orchestration

## Contributing

To extend the pipeline:

1. Add new filter types in `rule_integrator.py`
2. Customize prompts for your specific use case
3. Add new analysis metrics or categories
4. Integrate with different LLM providers

## License

This module is part of the pretrain_etl project and follows the same license terms.