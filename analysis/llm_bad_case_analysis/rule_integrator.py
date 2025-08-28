#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rule Integration Module for LLM-Generated Filtering Rules

This module converts LLM-generated filtering rules into executable functions
and integrates them with the existing data cleaning pipeline.
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from utils import read_jsonl, write_jsonl, write_json


class RuleIntegrator:
    """Integrates LLM-generated rules into the filtering pipeline"""
    
    def __init__(self, rules_dir: str = "./analysis_results"):
        """
        Initialize rule integrator
        
        Args:
            rules_dir: Directory containing analysis results with generated rules
        """
        self.rules_dir = Path(rules_dir)
        self.custom_filters = {}
        self.rule_stats = {}
    
    def load_rules_from_analysis(self, report_file: str) -> List[Dict[str, Any]]:
        """Load rules from analysis report file"""
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        return report.get('generated_rules', [])
    
    def convert_rule_to_filter(self, rule: Dict[str, Any]) -> Optional[Callable[[str], bool]]:
        """Convert a rule description to an executable filter function"""
        rule_name = rule.get('name', 'unknown_rule')
        implementation = rule.get('implementation', '')
        thresholds = rule.get('thresholds', {})
        
        try:
            # Create a filter function based on the rule implementation
            if 'import_ratio' in rule_name.lower() or 'mostly_imports' in implementation.lower():
                return self._create_import_ratio_filter(thresholds)
            elif 'comment_ratio' in rule_name.lower() or 'excessive_comments' in implementation.lower():
                return self._create_comment_ratio_filter(thresholds)
            elif 'trivial_variable' in rule_name.lower() or 'meaningless_vars' in implementation.lower():
                return self._create_trivial_variable_filter(thresholds)
            elif 'line_repetition' in rule_name.lower() or 'duplicated' in implementation.lower():
                return self._create_line_repetition_filter(thresholds)
            elif 'auto_generated' in rule_name.lower():
                return self._create_auto_generated_filter(thresholds)
            elif 'test_file' in rule_name.lower():
                return self._create_test_file_filter(thresholds)
            elif 'config_file' in rule_name.lower():
                return self._create_config_file_filter(thresholds)
            else:
                print(f"Warning: Could not convert rule '{rule_name}' to filter function")
                return None
                
        except Exception as e:
            print(f"Error converting rule '{rule_name}': {e}")
            return None
    
    def _create_import_ratio_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for excessive import statements"""
        max_ratio = thresholds.get('max_import_ratio', 0.5)
        min_lines = thresholds.get('min_lines', 10)
        
        def import_ratio_filter(text: str) -> bool:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < min_lines:
                return True  # Too short to judge
            
            import_lines = sum(1 for line in lines if 
                             line.startswith('import ') or 
                             line.startswith('from ') or
                             line.startswith('const ') and 'require(' in line)
            
            ratio = import_lines / len(lines)
            return ratio <= max_ratio
        
        return import_ratio_filter
    
    def _create_comment_ratio_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for excessive comments"""
        max_ratio = thresholds.get('max_comment_ratio', 0.6)
        min_lines = thresholds.get('min_lines', 10)
        
        def comment_ratio_filter(text: str) -> bool:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < min_lines:
                return True
            
            comment_lines = sum(1 for line in lines if 
                              line.startswith('//') or 
                              line.startswith('/*') or 
                              line.startswith('*') or
                              line.startswith('#'))
            
            ratio = comment_lines / len(lines)
            return ratio <= max_ratio
        
        return comment_ratio_filter
    
    def _create_trivial_variable_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for trivial variable names"""
        max_trivial_ratio = thresholds.get('max_trivial_ratio', 0.4)
        trivial_vars = thresholds.get('trivial_vars', ['a', 'b', 'c', 'd', 'e', 'x', 'y', 'z', 'i', 'j', 'k'])
        
        def trivial_variable_filter(text: str) -> bool:
            # Find variable declarations
            var_pattern = r'\b(?:let|const|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]'
            variables = re.findall(var_pattern, text)
            
            if len(variables) < 3:  # Too few variables to judge
                return True
            
            trivial_count = sum(1 for var in variables if var.lower() in trivial_vars)
            ratio = trivial_count / len(variables)
            
            return ratio <= max_trivial_ratio
        
        return trivial_variable_filter
    
    def _create_line_repetition_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for excessive line repetition"""
        max_repetition_ratio = thresholds.get('max_repetition_ratio', 0.3)
        min_lines = thresholds.get('min_lines', 10)
        
        def line_repetition_filter(text: str) -> bool:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < min_lines:
                return True
            
            line_counts = {}
            for line in lines:
                if len(line) > 10:  # Only count substantial lines
                    line_counts[line] = line_counts.get(line, 0) + 1
            
            repeated_lines = sum(count - 1 for count in line_counts.values() if count > 1)
            ratio = repeated_lines / len(lines)
            
            return ratio <= max_repetition_ratio
        
        return line_repetition_filter
    
    def _create_auto_generated_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for auto-generated code"""
        keywords = thresholds.get('keywords', [
            'auto-generated', 'autogenerated', 'do not edit', 'generated by',
            'this file was automatically generated', 'code generator',
            'scaffold', 'boilerplate'
        ])
        
        def auto_generated_filter(text: str) -> bool:
            text_lower = text.lower()
            return not any(keyword in text_lower for keyword in keywords)
        
        return auto_generated_filter
    
    def _create_test_file_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for test files"""
        test_keywords = thresholds.get('test_keywords', [
            'describe(', 'it(', 'test(', 'expect(', 'assert',
            'beforeEach', 'afterEach', 'jest', 'mocha'
        ])
        max_test_ratio = thresholds.get('max_test_ratio', 0.3)
        
        def test_file_filter(text: str) -> bool:
            lines = text.split('\n')
            test_lines = sum(1 for line in lines if any(keyword in line for keyword in test_keywords))
            
            if len(lines) == 0:
                return True
            
            ratio = test_lines / len(lines)
            return ratio <= max_test_ratio
        
        return test_file_filter
    
    def _create_config_file_filter(self, thresholds: Dict[str, Any]) -> Callable[[str], bool]:
        """Create filter for configuration files"""
        config_patterns = thresholds.get('config_patterns', [
            r'\"[a-zA-Z_]+\"\s*:\s*\"[^\"]*\"',  # JSON-like config
            r'[a-zA-Z_]+\s*=\s*[\"\'][^\"\'][\"\']',  # Key-value config
            r'module\.exports\s*=\s*{',  # Node.js config
        ])
        max_config_ratio = thresholds.get('max_config_ratio', 0.5)
        
        def config_file_filter(text: str) -> bool:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < 5:
                return True
            
            config_lines = 0
            for line in lines:
                if any(re.search(pattern, line) for pattern in config_patterns):
                    config_lines += 1
            
            ratio = config_lines / len(lines)
            return ratio <= max_config_ratio
        
        return config_file_filter
    
    def register_custom_filter(self, name: str, filter_func: Callable[[str], bool]):
        """Register a custom filter function"""
        self.custom_filters[name] = filter_func
        self.rule_stats[name] = {'applied': 0, 'filtered': 0}
    
    def apply_custom_filters(self, 
                           data: List[Dict[str, Any]], 
                           filter_names: List[str] = None) -> List[Dict[str, Any]]:
        """Apply custom filters to data"""
        if filter_names is None:
            filter_names = list(self.custom_filters.keys())
        
        filtered_data = []
        removed_by_filter = {name: [] for name in filter_names}
        
        for item in data:
            text = item.get('text', '')
            passed = True
            
            for filter_name in filter_names:
                if filter_name in self.custom_filters:
                    filter_func = self.custom_filters[filter_name]
                    self.rule_stats[filter_name]['applied'] += 1
                    
                    if not filter_func(text):
                        passed = False
                        removed_by_filter[filter_name].append(item)
                        self.rule_stats[filter_name]['filtered'] += 1
                        break
            
            if passed:
                filtered_data.append(item)
        
        # Save removal logs
        for filter_name, removed_items in removed_by_filter.items():
            if removed_items:
                log_file = self.rules_dir / f"removed_{filter_name}_filter.jsonl"
                write_jsonl(removed_items, str(log_file))
        
        return filtered_data
    
    def generate_filter_code(self, rules: List[Dict[str, Any]], output_file: str):
        """Generate Python code for the filters"""
        code_lines = [
            "# Auto-generated filter functions from LLM analysis",
            "# Generated at: " + datetime.now().isoformat(),
            "",
            "import re",
            "from typing import List, Dict, Any",
            ""
        ]
        
        for i, rule in enumerate(rules):
            rule_name = rule.get('name', f'rule_{i}').lower().replace(' ', '_')
            description = rule.get('description', 'No description')
            implementation = rule.get('implementation', '')
            
            code_lines.extend([
                f"def {rule_name}_filter(text: str) -> bool:",
                f'    \"\"\"{description}\"\"\"',
                f"    # Implementation: {implementation}",
                "    # TODO: Implement this filter based on the rule description",
                "    return True  # Placeholder - implement actual logic",
                ""
            ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(code_lines))
        
        print(f"Generated filter code saved to {output_file}")
    
    def get_filter_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for applied filters"""
        return self.rule_stats.copy()
    
    def save_integration_report(self, output_file: str):
        """Save integration report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'registered_filters': list(self.custom_filters.keys()),
            'filter_stats': self.rule_stats,
            'total_filters': len(self.custom_filters)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def integrate_rules_from_analysis(analysis_report_file: str, 
                                data_file: str,
                                output_file: str,
                                rules_dir: str = "./analysis_results"):
    """Complete integration workflow"""
    print(f"Integrating rules from {analysis_report_file}...")
    
    # Initialize integrator
    integrator = RuleIntegrator(rules_dir)
    
    # Load rules from analysis
    rules = integrator.load_rules_from_analysis(analysis_report_file)
    print(f"Loaded {len(rules)} rules from analysis.")
    
    # Convert rules to filters
    for rule in rules:
        filter_func = integrator.convert_rule_to_filter(rule)
        if filter_func:
            rule_name = rule.get('name', 'unknown').lower().replace(' ', '_')
            integrator.register_custom_filter(rule_name, filter_func)
    
    print(f"Registered {len(integrator.custom_filters)} custom filters.")
    
    # Apply filters to data
    print(f"Loading data from {data_file}...")
    data = read_jsonl(data_file)
    print(f"Loaded {len(data)} records.")
    
    print("Applying custom filters...")
    filtered_data = integrator.apply_custom_filters(data)
    
    print(f"Filtered data: {len(data)} -> {len(filtered_data)} records")
    print(f"Removed: {len(data) - len(filtered_data)} records")
    
    # Save results
    write_jsonl(filtered_data, output_file)
    print(f"Filtered data saved to {output_file}")
    
    # Save integration report
    report_file = Path(rules_dir) / "integration_report.json"
    integrator.save_integration_report(str(report_file))
    
    # Print statistics
    stats = integrator.get_filter_stats()
    print("\n=== Filter Statistics ===")
    for filter_name, stat in stats.items():
        if stat['applied'] > 0:
            filter_rate = stat['filtered'] / stat['applied'] * 100
            print(f"{filter_name}: {stat['filtered']}/{stat['applied']} ({filter_rate:.1f}%) filtered")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Integrate LLM-generated rules into filtering pipeline')
    parser.add_argument('analysis_report', help='Path to analysis report JSON file')
    parser.add_argument('data_file', help='Path to input data JSONL file')
    parser.add_argument('output_file', help='Path to output filtered data JSONL file')
    parser.add_argument('--rules-dir', default='./analysis_results', help='Rules directory')
    
    args = parser.parse_args()
    
    integrate_rules_from_analysis(
        analysis_report_file=args.analysis_report,
        data_file=args.data_file,
        output_file=args.output_file,
        rules_dir=args.rules_dir
    )