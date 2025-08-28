#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-based Bad Case Analysis Pipeline for ArkTS Code Corpus Cleaning

This module provides an automated pipeline to:
1. Sample random entries from raw data
2. Use LLM to identify and classify dirty data
3. Generate filtering rules based on bad cases
4. Integrate with existing cleaning pipeline
"""

import os
import sys
import json
import random
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils import read_jsonl, write_jsonl, write_json
from llm_chat.chat_client import create_chat_client


@dataclass
class BadCaseResult:
    """Bad case analysis result"""
    is_dirty: bool
    category: str
    reason: str
    confidence: float
    suggested_filter: Optional[str] = None


@dataclass
class AnalysisReport:
    """Analysis report for a batch of samples"""
    total_samples: int
    dirty_count: int
    clean_count: int
    categories: Dict[str, int]
    bad_cases: List[Dict[str, Any]]
    generated_rules: List[str]
    timestamp: str


class LLMBadCaseAnalyzer:
    """LLM-based bad case analyzer for code corpus cleaning"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "qwen3-coder-plus",
                 temperature: float = 0.3,
                 output_dir: str = "./analysis_results"):
        """
        Initialize the LLM bad case analyzer
        
        Args:
            api_key: LLM API key
            model: Model name to use
            temperature: Generation temperature
            output_dir: Directory to save analysis results
        """
        self.llm_client = create_chat_client(
            api_key=api_key,
            model=model,
            temperature=temperature
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Default prompts (can be customized later)
        self.detection_prompt = self._get_default_detection_prompt()
        self.rule_generation_prompt = self._get_default_rule_generation_prompt()
    
    def _get_default_detection_prompt(self) -> str:
        """Get default prompt for dirty data detection"""
        return """
You are an expert code quality analyzer for ArkTS/TypeScript code corpus cleaning.

Analyze the following code sample and determine if it's dirty data that should be filtered out from a pretraining corpus.

Consider these quality issues:
1. Auto-generated code (boilerplate, scaffolding)
2. Test files with minimal logic
3. Configuration files or data files
4. Incomplete or broken code
5. Code with excessive comments/documentation ratio
6. Trivial examples or hello-world code
7. Code with poor formatting or structure
8. Non-meaningful variable names (a, b, c, etc.)
9. Code that's mostly imports/declarations
10. Duplicated or template code

Respond in JSON format:
{{
    "is_dirty": boolean,
    "category": "string (one of: auto_generated, test_code, config_file, incomplete, excessive_comments, trivial, poor_format, meaningless_vars, mostly_imports, duplicated, clean)",
    "reason": "string (detailed explanation)",
    "confidence": float (0.0-1.0)
}}

Code to analyze:
```
{code}
```
"""
    
    def _get_default_rule_generation_prompt(self) -> str:
        """Get default prompt for rule generation"""
        return """
You are an expert in designing code filtering rules for corpus cleaning pipelines.

Based on the following bad cases identified in ArkTS/TypeScript code, generate specific, implementable filtering rules.

Bad cases summary:
{bad_cases_summary}

Generate filtering rules in the following format:
1. Rule name and description
2. Implementation logic (pseudocode or Python)
3. Threshold values if applicable
4. Expected impact

Focus on rules that can be implemented programmatically and are generalizable.

Respond in JSON format:
{{
    "rules": [
        {{
            "name": "string",
            "description": "string",
            "implementation": "string (pseudocode or Python)",
            "thresholds": {{"param": value}},
            "expected_impact": "string"
        }}
    ]
}}
"""
    
    def sample_data(self, 
                   data: List[Dict[str, Any]], 
                   sample_size: int = 100,
                   seed: int = 42) -> List[Dict[str, Any]]:
        """Randomly sample data entries"""
        random.seed(seed)
        if len(data) <= sample_size:
            return data.copy()
        return random.sample(data, sample_size)
    
    def analyze_sample(self, sample: Dict[str, Any]) -> BadCaseResult:
        """Analyze a single sample using LLM"""
        code = sample.get('text', '')
        prompt = self.detection_prompt.format(code=code)
        
        try:
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message="You are a code quality expert. Respond only in valid JSON format."
            )
            
            # Parse LLM response
            result_data = json.loads(response)
            
            return BadCaseResult(
                is_dirty=result_data.get('is_dirty', False),
                category=result_data.get('category', 'unknown'),
                reason=result_data.get('reason', ''),
                confidence=result_data.get('confidence', 0.0)
            )
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"Error analyzing sample: {e}")
            return BadCaseResult(
                is_dirty=False,
                category='error',
                reason=f'Analysis failed: {str(e)}',
                confidence=0.0
            )
    
    def analyze_batch(self, 
                     samples: List[Dict[str, Any]],
                     batch_name: str = None) -> AnalysisReport:
        """Analyze a batch of samples"""
        if batch_name is None:
            batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Analyzing {len(samples)} samples...")
        
        bad_cases = []
        categories = {}
        dirty_count = 0
        
        for i, sample in enumerate(samples):
            print(f"Analyzing sample {i+1}/{len(samples)}...", end='\r')
            
            result = self.analyze_sample(sample)
            
            if result.is_dirty:
                dirty_count += 1
                bad_case = {
                    'sample_id': i,
                    'original_data': sample,
                    'analysis': {
                        'category': result.category,
                        'reason': result.reason,
                        'confidence': result.confidence
                    }
                }
                bad_cases.append(bad_case)
            
            # Count categories
            category = result.category
            categories[category] = categories.get(category, 0) + 1
        
        print(f"\nAnalysis complete. Found {dirty_count} dirty samples out of {len(samples)}.")
        
        # Generate filtering rules based on bad cases
        generated_rules = self._generate_rules(bad_cases) if bad_cases else []
        
        report = AnalysisReport(
            total_samples=len(samples),
            dirty_count=dirty_count,
            clean_count=len(samples) - dirty_count,
            categories=categories,
            bad_cases=bad_cases,
            generated_rules=generated_rules,
            timestamp=datetime.now().isoformat()
        )
        
        # Save results
        self._save_analysis_results(report, batch_name)
        
        return report
    
    def _generate_rules(self, bad_cases: List[Dict[str, Any]]) -> List[str]:
        """Generate filtering rules based on bad cases"""
        if not bad_cases:
            return []
        
        # Summarize bad cases
        categories_summary = {}
        for case in bad_cases:
            category = case['analysis']['category']
            if category not in categories_summary:
                categories_summary[category] = []
            categories_summary[category].append(case['analysis']['reason'])
        
        summary_text = "\n".join([
            f"Category: {cat}\nCount: {len(reasons)}\nReasons: {'; '.join(reasons[:3])}\n"
            for cat, reasons in categories_summary.items()
        ])
        
        prompt = self.rule_generation_prompt.format(bad_cases_summary=summary_text)
        
        try:
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message="You are a filtering rule expert. Respond only in valid JSON format."
            )
            
            result_data = json.loads(response)
            return result_data.get('rules', [])
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating rules: {e}")
            return []
    
    def _save_analysis_results(self, report: AnalysisReport, batch_name: str):
        """Save analysis results to files"""
        # Save full report
        report_file = self.output_dir / f"{batch_name}_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_samples': report.total_samples,
                'dirty_count': report.dirty_count,
                'clean_count': report.clean_count,
                'categories': report.categories,
                'generated_rules': report.generated_rules,
                'timestamp': report.timestamp
            }, f, indent=2, ensure_ascii=False)
        
        # Save bad cases
        if report.bad_cases:
            bad_cases_file = self.output_dir / f"{batch_name}_bad_cases.jsonl"
            write_jsonl(report.bad_cases, str(bad_cases_file))
        
        print(f"Results saved to {self.output_dir}")
    
    def run_analysis_pipeline(self, 
                            data_file: str,
                            sample_size: int = 100,
                            batch_name: str = None) -> AnalysisReport:
        """Run the complete analysis pipeline"""
        print(f"Loading data from {data_file}...")
        data = read_jsonl(data_file)
        print(f"Loaded {len(data)} records.")
        
        print(f"Sampling {sample_size} records...")
        samples = self.sample_data(data, sample_size)
        
        return self.analyze_batch(samples, batch_name)


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM-based Bad Case Analysis Pipeline')
    parser.add_argument('data_file', help='Path to input JSONL data file')
    parser.add_argument('--sample-size', type=int, default=100, help='Number of samples to analyze')
    parser.add_argument('--batch-name', help='Name for this analysis batch')
    parser.add_argument('--output-dir', default='./analysis_results', help='Output directory')
    parser.add_argument('--model', default='qwen3-coder-plus', help='LLM model to use')
    parser.add_argument('--temperature', type=float, default=0.3, help='Generation temperature')
    
    args = parser.parse_args()
    
    analyzer = LLMBadCaseAnalyzer(
        model=args.model,
        temperature=args.temperature,
        output_dir=args.output_dir
    )
    
    report = analyzer.run_analysis_pipeline(
        data_file=args.data_file,
        sample_size=args.sample_size,
        batch_name=args.batch_name
    )
    
    print("\n=== Analysis Summary ===")
    print(f"Total samples: {report.total_samples}")
    print(f"Dirty samples: {report.dirty_count} ({report.dirty_count/report.total_samples*100:.1f}%)")
    print(f"Clean samples: {report.clean_count} ({report.clean_count/report.total_samples*100:.1f}%)")
    print("\nCategories:")
    for category, count in report.categories.items():
        print(f"  {category}: {count}")
    print(f"\nGenerated {len(report.generated_rules)} filtering rules.")


if __name__ == '__main__':
    main()