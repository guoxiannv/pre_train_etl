#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete LLM-based Bad Case Analysis Pipeline

This module orchestrates the complete workflow:
1. Sample data from corpus
2. Analyze with LLM to identify bad cases
3. Generate filtering rules
4. Integrate rules into cleaning pipeline
5. Apply enhanced cleaning to full dataset
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils import read_jsonl, write_jsonl, write_json
from analysis.llm_bad_case_analysis.llm_bad_case_analyzer import LLMBadCaseAnalyzer
from analysis.llm_bad_case_analysis.rule_integrator import RuleIntegrator
from data_processing.preprocess.pre_process_modified import data_clean_pipeline


class BadCasePipeline:
    """Complete bad case analysis and filtering pipeline"""
    
    def __init__(self, 
                 output_dir: str = "./pipeline_results",
                 api_key: Optional[str] = None,
                 model: str = "qwen3-coder-plus",
                 temperature: float = 0.3):
        """
        Initialize the complete pipeline
        
        Args:
            output_dir: Directory to save all pipeline results
            api_key: LLM API key
            model: LLM model name
            temperature: Generation temperature
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.analyzer = LLMBadCaseAnalyzer(
            api_key=api_key,
            model=model,
            temperature=temperature,
            output_dir=str(self.output_dir / "analysis")
        )
        
        self.integrator = RuleIntegrator(
            rules_dir=str(self.output_dir / "analysis")
        )
        
        self.pipeline_log = []
    
    def log_step(self, step: str, details: Dict[str, Any]):
        """Log pipeline step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'details': details
        }
        self.pipeline_log.append(log_entry)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}: {details.get('message', '')}")
    
    def run_analysis_round(self, 
                          data_file: str,
                          sample_size: int = 100,
                          round_name: str = None) -> Dict[str, Any]:
        """
        Run one round of bad case analysis
        
        Args:
            data_file: Path to input data file
            sample_size: Number of samples to analyze
            round_name: Name for this analysis round
            
        Returns:
            Analysis results summary
        """
        if round_name is None:
            round_name = f"round_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.log_step("START_ANALYSIS", {
            'message': f'Starting analysis round: {round_name}',
            'data_file': data_file,
            'sample_size': sample_size
        })
        
        # Run LLM analysis
        report = self.analyzer.run_analysis_pipeline(
            data_file=data_file,
            sample_size=sample_size,
            batch_name=round_name
        )
        
        self.log_step("ANALYSIS_COMPLETE", {
            'message': f'Analysis complete for {round_name}',
            'total_samples': report.total_samples,
            'dirty_count': report.dirty_count,
            'clean_count': report.clean_count,
            'rules_generated': len(report.generated_rules)
        })
        
        return {
            'round_name': round_name,
            'report': report,
            'report_file': str(self.output_dir / "analysis" / f"{round_name}_report.json"),
            'bad_cases_file': str(self.output_dir / "analysis" / f"{round_name}_bad_cases.jsonl")
        }
    
    def integrate_rules(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Integrate rules from multiple analysis rounds
        
        Args:
            analysis_results: List of analysis results from run_analysis_round
            
        Returns:
            Integration results
        """
        self.log_step("START_INTEGRATION", {
            'message': f'Integrating rules from {len(analysis_results)} analysis rounds'
        })
        
        all_rules = []
        total_bad_cases = 0
        
        # Collect all rules from analysis rounds
        for result in analysis_results:
            report = result['report']
            all_rules.extend(report.generated_rules)
            total_bad_cases += report.dirty_count
        
        # Remove duplicate rules (by name)
        unique_rules = []
        seen_names = set()
        for rule in all_rules:
            rule_name = rule.get('name', 'unknown')
            if rule_name not in seen_names:
                unique_rules.append(rule)
                seen_names.add(rule_name)
        
        self.log_step("RULES_COLLECTED", {
            'message': f'Collected {len(unique_rules)} unique rules from {len(all_rules)} total rules',
            'total_bad_cases': total_bad_cases
        })
        
        # Convert rules to filter functions
        registered_filters = 0
        for rule in unique_rules:
            filter_func = self.integrator.convert_rule_to_filter(rule)
            if filter_func:
                rule_name = rule.get('name', 'unknown').lower().replace(' ', '_')
                self.integrator.register_custom_filter(rule_name, filter_func)
                registered_filters += 1
        
        self.log_step("FILTERS_REGISTERED", {
            'message': f'Registered {registered_filters} filter functions',
            'total_rules': len(unique_rules)
        })
        
        return {
            'total_rules': len(unique_rules),
            'registered_filters': registered_filters,
            'filter_names': list(self.integrator.custom_filters.keys())
        }
    
    def apply_enhanced_cleaning(self, 
                              data_file: str,
                              output_file: str,
                              use_existing_pipeline: bool = True) -> Dict[str, Any]:
        """
        Apply enhanced cleaning with both existing and LLM-generated filters
        
        Args:
            data_file: Input data file
            output_file: Output cleaned data file
            use_existing_pipeline: Whether to use existing heuristic filters first
            
        Returns:
            Cleaning results summary
        """
        self.log_step("START_CLEANING", {
            'message': f'Starting enhanced cleaning',
            'input_file': data_file,
            'output_file': output_file,
            'use_existing_pipeline': use_existing_pipeline
        })
        
        # Load data
        data = read_jsonl(data_file)
        original_count = len(data)
        
        # Apply existing pipeline first if requested
        if use_existing_pipeline:
            self.log_step("EXISTING_PIPELINE", {
                'message': 'Applying existing heuristic filters'
            })
            
            data = data_clean_pipeline(
                corpus=data,
                out_dir=str(self.output_dir / "existing_filter_logs"),
                preprocess_only=False
            )
            
            after_existing = len(data)
            self.log_step("EXISTING_COMPLETE", {
                'message': f'Existing pipeline: {original_count} -> {after_existing} records',
                'removed': original_count - after_existing
            })
        else:
            after_existing = original_count
        
        # Apply LLM-generated filters
        if self.integrator.custom_filters:
            self.log_step("LLM_FILTERS", {
                'message': f'Applying {len(self.integrator.custom_filters)} LLM-generated filters'
            })
            
            data = self.integrator.apply_custom_filters(data)
            
            after_llm = len(data)
            self.log_step("LLM_COMPLETE", {
                'message': f'LLM filters: {after_existing} -> {after_llm} records',
                'removed': after_existing - after_llm
            })
        else:
            after_llm = after_existing
            self.log_step("NO_LLM_FILTERS", {
                'message': 'No LLM filters to apply'
            })
        
        # Save cleaned data
        write_jsonl(data, output_file)
        
        final_count = len(data)
        total_removed = original_count - final_count
        removal_rate = (total_removed / original_count) * 100 if original_count > 0 else 0
        
        self.log_step("CLEANING_COMPLETE", {
            'message': f'Enhanced cleaning complete',
            'original_count': original_count,
            'final_count': final_count,
            'total_removed': total_removed,
            'removal_rate': f'{removal_rate:.1f}%'
        })
        
        return {
            'original_count': original_count,
            'after_existing': after_existing,
            'final_count': final_count,
            'total_removed': total_removed,
            'removal_rate': removal_rate,
            'filter_stats': self.integrator.get_filter_stats()
        }
    
    def run_complete_pipeline(self, 
                            data_file: str,
                            output_file: str,
                            num_rounds: int = 1,
                            sample_size: int = 100,
                            use_existing_pipeline: bool = True) -> Dict[str, Any]:
        """
        Run the complete pipeline from analysis to final cleaning
        
        Args:
            data_file: Input data file
            output_file: Final cleaned data output file
            num_rounds: Number of analysis rounds to run
            sample_size: Sample size for each analysis round
            use_existing_pipeline: Whether to use existing heuristic filters
            
        Returns:
            Complete pipeline results
        """
        pipeline_start = datetime.now()
        
        self.log_step("PIPELINE_START", {
            'message': f'Starting complete bad case analysis pipeline',
            'data_file': data_file,
            'output_file': output_file,
            'num_rounds': num_rounds,
            'sample_size': sample_size
        })
        
        # Run analysis rounds
        analysis_results = []
        for round_num in range(num_rounds):
            round_name = f"round_{round_num + 1}"
            result = self.run_analysis_round(
                data_file=data_file,
                sample_size=sample_size,
                round_name=round_name
            )
            analysis_results.append(result)
        
        # Integrate rules
        integration_result = self.integrate_rules(analysis_results)
        
        # Apply enhanced cleaning
        cleaning_result = self.apply_enhanced_cleaning(
            data_file=data_file,
            output_file=output_file,
            use_existing_pipeline=use_existing_pipeline
        )
        
        # Generate final report
        pipeline_end = datetime.now()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        final_report = {
            'pipeline_info': {
                'start_time': pipeline_start.isoformat(),
                'end_time': pipeline_end.isoformat(),
                'duration_seconds': duration,
                'num_rounds': num_rounds,
                'sample_size': sample_size
            },
            'analysis_summary': {
                'total_samples_analyzed': num_rounds * sample_size,
                'total_bad_cases': sum(r['report'].dirty_count for r in analysis_results),
                'categories_found': {}
            },
            'integration_summary': integration_result,
            'cleaning_summary': cleaning_result,
            'pipeline_log': self.pipeline_log
        }
        
        # Aggregate categories from all rounds
        all_categories = {}
        for result in analysis_results:
            for category, count in result['report'].categories.items():
                all_categories[category] = all_categories.get(category, 0) + count
        final_report['analysis_summary']['categories_found'] = all_categories
        
        # Save final report
        report_file = self.output_dir / "pipeline_final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        self.log_step("PIPELINE_COMPLETE", {
            'message': f'Complete pipeline finished in {duration:.1f} seconds',
            'final_report': str(report_file)
        })
        
        return final_report
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of pipeline results"""
        print("\n" + "="*60)
        print("         BAD CASE ANALYSIS PIPELINE SUMMARY")
        print("="*60)
        
        # Pipeline info
        info = results['pipeline_info']
        print(f"Duration: {info['duration_seconds']:.1f} seconds")
        print(f"Analysis rounds: {info['num_rounds']}")
        print(f"Sample size per round: {info['sample_size']}")
        
        # Analysis summary
        analysis = results['analysis_summary']
        print(f"\nTotal samples analyzed: {analysis['total_samples_analyzed']}")
        print(f"Total bad cases found: {analysis['total_bad_cases']}")
        print("\nBad case categories:")
        for category, count in analysis['categories_found'].items():
            print(f"  {category}: {count}")
        
        # Integration summary
        integration = results['integration_summary']
        print(f"\nRules generated: {integration['total_rules']}")
        print(f"Filters registered: {integration['registered_filters']}")
        
        # Cleaning summary
        cleaning = results['cleaning_summary']
        print(f"\nData cleaning results:")
        print(f"  Original records: {cleaning['original_count']:,}")
        print(f"  Final records: {cleaning['final_count']:,}")
        print(f"  Removed: {cleaning['total_removed']:,} ({cleaning['removal_rate']:.1f}%)")
        
        # Filter statistics
        if cleaning['filter_stats']:
            print("\nFilter performance:")
            for filter_name, stats in cleaning['filter_stats'].items():
                if stats['applied'] > 0:
                    rate = stats['filtered'] / stats['applied'] * 100
                    print(f"  {filter_name}: {stats['filtered']}/{stats['applied']} ({rate:.1f}%)")
        
        print("="*60)


def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete LLM-based Bad Case Analysis Pipeline')
    parser.add_argument('data_file', help='Path to input JSONL data file')
    parser.add_argument('output_file', help='Path to output cleaned JSONL file')
    parser.add_argument('--rounds', type=int, default=1, help='Number of analysis rounds')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size per round')
    parser.add_argument('--output-dir', default='./pipeline_results', help='Output directory')
    parser.add_argument('--model', default='qwen3-coder-plus', help='LLM model to use')
    parser.add_argument('--temperature', type=float, default=0.3, help='Generation temperature')
    parser.add_argument('--skip-existing', action='store_true', help='Skip existing heuristic filters')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = BadCasePipeline(
        output_dir=args.output_dir,
        model=args.model,
        temperature=args.temperature
    )
    
    # Run complete pipeline
    results = pipeline.run_complete_pipeline(
        data_file=args.data_file,
        output_file=args.output_file,
        num_rounds=args.rounds,
        sample_size=args.sample_size,
        use_existing_pipeline=not args.skip_existing
    )
    
    # Print summary
    pipeline.print_summary(results)


if __name__ == '__main__':
    main()