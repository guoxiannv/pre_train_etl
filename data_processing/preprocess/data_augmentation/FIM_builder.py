import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import *
from tree_sitter import Language, Parser
import tree_sitter_typescript as tst
import random
import re
import json

tree_sitter_language = Language(tst.language_typescript())
parser = Parser()
parser.language = tree_sitter_language

def extract_functions_from_ast(node, source_code):
    """Extract all function definitions from AST"""
    functions = []
    
    def is_empty_function(function_code):
        """Check if function is empty or minimal (like () => { })"""
        # Remove whitespace and newlines for analysis
        cleaned = function_code.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        
        # Check for very short functions (likely empty)
        if len(cleaned) < 10:
            return True
        
        # Extract function body (content between { and })
        body_match = re.search(r'\{([^}]*)\}', function_code)
        if body_match:
            body = body_match.group(1).strip()
            
            # Check if body is empty or contains only return/whitespace
            if not body:  # Completely empty body
                return True
            
            # Remove whitespace and check common empty patterns
            clean_body = re.sub(r'\s+', '', body)
            empty_body_patterns = [
                 '',  # empty
                 'return;',
                 'return',
                 '//.*',  # only comments
                 r'/\*.*\*/',  # only comments
             ]
            
            if clean_body.lower() in [p.lower() for p in empty_body_patterns]:
                return True
            
            # Check if body only contains comments
            if re.match(r'^\s*(//.*|/\*.*\*/)?\s*$', body):
                return True
        
        # Check for arrow functions with empty body
        if '=>' in function_code:
            # Extract part after =>
            arrow_parts = function_code.split('=>', 1)
            if len(arrow_parts) > 1:
                arrow_body = arrow_parts[1].strip()
                if arrow_body in ['{}', '{ }', '{return;}', '{return}']:
                    return True
        
        return False
    
    def traverse(node):
        # Check for function declarations and method definitions
        if node.type in ['function_declaration', 'method_definition', 'arrow_function', 'function_expression']:
            start_byte = node.start_byte
            end_byte = node.end_byte
            function_code = source_code[start_byte:end_byte]
            
            # Skip empty or minimal functions
            if not is_empty_function(function_code):
                functions.append({
                    'code': function_code,
                    'start_byte': start_byte,
                    'end_byte': end_byte,
                    'start_point': node.start_point,
                    'end_point': node.end_point
                })
        
        # Recursively traverse child nodes
        for child in node.children:
            traverse(child)
    
    traverse(node)
    return functions

def build_fim_data(source_code, functions):
    """Build FIM (Fill-In-the-Middle) data from source code and extracted functions"""
    if not functions:
        return None
    
    # Randomly select one function as the middle part
    selected_function = random.choice(functions)
    
    # Extract prefix (code before the function)
    prefix = source_code[:selected_function['start_byte']]
    
    # Extract middle (the selected function)
    middle = source_code[selected_function['start_byte']:selected_function['end_byte']]
    
    # Extract suffix (code after the function)
    suffix = source_code[selected_function['end_byte']:]
    
    return {
        'prefix': prefix,
        'middle': middle,
        'suffix': suffix,
        'function_info': {
            'start_byte': selected_function['start_byte'],
            'end_byte': selected_function['end_byte'],
            'start_line': selected_function['start_point'][0] + 1,  # Convert to 1-indexed
            'end_line': selected_function['end_point'][0] + 1
        }
    }

def process_code_samples(input_file, output_file):
    """Process multiple code samples and generate FIM data"""
    data = read_jsonl(input_file)
    fim_results = []
    
    for i, item in enumerate(data):
        code_content = item.get('text', '')
        id = item.get('id', '')
        if not code_content:
            continue
            
        # Parse the code into syntax tree
        syntax_tree = parser.parse(code_content.encode('utf-8'))
        
        # Extract all functions from AST
        functions = extract_functions_from_ast(syntax_tree.root_node, code_content)
        
        if functions:
            # Build FIM data
            fim_data = build_fim_data(code_content, functions)
            if fim_data:
                fim_data['source_id'] = id
                fim_data['fim_type'] = "function"
                fim_results.append(fim_data)
                print(f"Processed sample {i}: Found {len(functions)} functions")
        else:
            print(f"No functions found in sample {i}")
    
    # Save results
    write_jsonl(fim_results, output_file)
    print(f"Generated {len(fim_results)} FIM samples and saved to {output_file}")
    return fim_results

# Example usage
if __name__ == "__main__":
    input_file = 'code_data/cleaned_data/test_200.jsonl'
    output_file = 'code_data/cleaned_data/fim_data.jsonl'
    
    # Process all samples
    results = process_code_samples(input_file, output_file)
    
    # Display a sample result
    if results:
        print("\n=== Sample FIM Result ===")
        sample = results[0]
        print(f"Prefix length: {len(sample['prefix'])} characters")
        print(f"Middle length: {len(sample['middle'])} characters")
        print(f"Suffix length: {len(sample['suffix'])} characters")
        print(f"Function at lines {sample['function_info']['start_line']}-{sample['function_info']['end_line']}")
        print(f"\nMiddle (selected function):\n{sample['middle'][:200]}..." if len(sample['middle']) > 200 else f"\nMiddle (selected function):\n{sample['middle']}")

