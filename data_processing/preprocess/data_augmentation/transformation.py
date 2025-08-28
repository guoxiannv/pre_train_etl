import sys
import os
import random
import string
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import *
from tree_sitter import Language, Parser
import tree_sitter_typescript as tst

tree_sitter_language = Language(tst.language_typescript())
parser = Parser()
parser.language = tree_sitter_language

class VariableRenamer:
    def __init__(self, code_content):
        self.code_content = code_content
        self.syntax_tree = parser.parse(code_content.encode('utf-8'))
        self.variable_mappings = {}
        self.used_names = set()
    
    def generate_random_name(self, length=8):
        """Generate a random variable name."""
        while True:
            name = ''.join(random.choices(string.ascii_letters, k=length))
            if name not in self.used_names and not name[0].isdigit():
                self.used_names.add(name)
                return name
    
    def find_variables_to_rename(self):
        """Find all variables that can be renamed."""
        variables_to_rename = []
        
        def traverse(node, parent=None):
            if node.type == 'identifier':
                text = self.code_content[node.start_byte:node.end_byte]
                parent_type = parent.type if parent else None
                
                # Skip if it's a property name or method name
                if parent and parent.type in ['property_identifier', 'method_definition', 'call_expression']:
                    return
                
                # Skip built-in types and keywords
                if text in ['console', 'window', 'document', 'process', 'require', 'module', 'exports']:
                    return
                
                # Skip if it's a type identifier in type annotations
                if self._is_in_type_context(node):
                    return
                
                # Skip import/export identifiers
                if self._is_in_import_or_export(node):
                    return
                
                # Skip property names in object literals
                if self._is_object_property_key(node):
                    return
                
                # Case 1: Variable declarations (const, let, var)
                if self._is_variable_declaration(node, parent):
                    variables_to_rename.append({
                        'type': 'variable_declaration',
                        'name': text,
                        'node': node,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte
                    })
                
                # Case 2: Function parameters
                elif self._is_function_parameter(node, parent):
                    variables_to_rename.append({
                        'type': 'parameter',
                        'name': text,
                        'node': node,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte
                    })
                
            
            # Process all children
            for child in node.children:
                traverse(child, node)
        
        # Use tree-sitter query for more accurate parameter detection
        try:
            from tree_sitter import Query
            query = Query(
                tree_sitter_language,
                """
                (variable_declarator
                    name: (identifier) @var_decl)
                (required_parameter
                    (identifier) @param)
                (optional_parameter
                    (identifier) @param)
                """
            )
            
            matches = query.matches(self.syntax_tree.root_node)
            for match in matches:
                for capture_name, nodes in match.items():
                    for node in nodes:
                        text = self.code_content[node.start_byte:node.end_byte]
                        if capture_name == 'var_decl' and not self._should_skip_identifier(node, text):
                            variables_to_rename.append({
                                'type': 'variable_declaration',
                                'name': text,
                                'node': node,
                                'start_byte': node.start_byte,
                                'end_byte': node.end_byte
                            })
                        elif capture_name in ['param'] and not self._should_skip_identifier(node, text):
                            variables_to_rename.append({
                                'type': 'parameter',
                                'name': text,
                                'node': node,
                                'start_byte': node.start_byte,
                                'end_byte': node.end_byte
                            })
        except Exception as e:
            # Fallback to manual traversal if query fails
            pass
        
        # Remove duplicates based on name
        seen = set()
        unique_variables = []
        for var in variables_to_rename:
            if var['name'] not in seen:
                seen.add(var['name'])
                unique_variables.append(var)
        
        return unique_variables
    
    def _should_skip_identifier(self, node, text):
        """Determine if an identifier should be skipped."""
        # Skip built-in types and keywords
        skip_keywords = [
            'console', 'window', 'document', 'process', 'require', 'module', 'exports',
            'Promise', 'Set', 'Map', 'Array', 'Object', 'String', 'Number', 'Boolean',
            'Error', 'Date', 'RegExp', 'JSON', 'Math', 'parseInt', 'parseFloat'
        ]
        
        if text in skip_keywords:
            return True
        
        # Skip if in type context
        if self._is_in_type_context(node):
            return True
        
        # Skip if in import/export
        if self._is_in_import_or_export(node):
            return True
        
        # Skip property names
        if self._is_object_property_key(node):
            return True
        
        return False
    
    def _is_in_type_context(self, node):
        """Check if identifier is in type annotation or similar context."""
        current = node
        while current:
            parent = current.parent
            if parent and parent.type in ['type_annotation', 'type_identifier', 'import_statement', 'export_statement']:
                return True
            current = parent
        return False
    
    def _is_object_property_key(self, node):
        """Check if identifier is used as object property key."""
        parent = node.parent
        if parent and parent.type == 'pair' and parent.children[0] == node:
            return True
        return False
    
    def _is_variable_declaration(self, node, parent):
        """Check if this identifier is a variable being declared."""
        if not parent:
            return False
        
        # Check for const/let/var declarations
        if parent.type == 'variable_declarator':
            # Ensure this is the identifier being declared, not the value
            grandparent = self._get_parent(parent)
            if grandparent and grandparent.type in ['lexical_declaration', 'variable_declaration']:
                return True
        
        return False
    
    def _is_function_parameter(self, node, parent):
        """Check if this identifier is a function parameter."""
        if not parent:
            return False
        
        # Direct parameter in required_parameter
        if parent.type == 'required_parameter':
            return True
        
        # Parameter in formal_parameters
        if parent.type == 'identifier':
            # Check if we're inside formal_parameters
            current = parent
            while current:
                if current.type == 'formal_parameters':
                    return True
                if current.type in ['class_body', 'program']:
                    break
                current = current.parent
        
        # Parameter with type annotation
        if parent.type == 'identifier' and parent.parent and parent.parent.type == 'required_parameter':
            return True
        
        return False
    
    def _is_local_variable(self, node, parent):
        """Check if this is a local variable usage."""
        if not parent:
            return False
        
        # Skip if it's a property access like obj.property
        if self._is_property_access(node):
            return False
        
        # Skip if it's a method name
        if self._is_method_name(node):
            return False
        
        # Skip if it's a class name or type identifier
        if parent.type == 'type_identifier' or parent.type == 'class_declaration':
            return False
        
        # Check if it's a variable usage (not declaration, not parameter)
        text = self.code_content[node.start_byte:node.end_byte]
        
        # Skip common keywords and built-ins
        skip_keywords = [
            'console', 'window', 'document', 'process', 'require', 'module', 'exports',
            'Promise', 'Set', 'Map', 'Array', 'Object', 'String', 'Number', 'Boolean',
            'Error', 'Date', 'RegExp', 'JSON', 'Math', 'parseInt', 'parseFloat'
        ]
        
        if text in skip_keywords:
            return False
        
        # Skip if it's a type in type annotations
        if self._is_type_identifier(node):
            return False
        
        return True
    
    def _is_type_identifier(self, node):
        """Check if this identifier is used as a type."""
        if not node.parent:
            return False
        
        # Check various contexts where identifiers are used as types
        parent = node.parent
        
        # Type annotation context
        if parent.type == 'type_annotation' or parent.type == 'type_identifier':
            return True
        
        # Generic type parameters
        if parent.type == 'generic_type' or parent.type == 'type_arguments':
            return True
        
        return False
    
    def _is_in_import_or_export(self, node):
        """Check if identifier is part of import/export statement."""
        current = node
        while current:
            if current.type in ['import_statement', 'export_statement']:
                return True
            current = current.parent
        return False
    
    def _is_property_access(self, node):
        """Check if this identifier is part of a property access."""
        if not node.parent:
            return False
        
        # Check for member_expression pattern
        parent = node.parent
        if parent.type == 'member_expression':
            # Check if this is the property part (after dot)
            siblings = list(parent.children)
            if len(siblings) >= 2 and siblings[-1] == node and siblings[-2].type == '.':
                return True
        
        return False
    
    def _is_method_name(self, node):
        """Check if this identifier is a method name."""
        if not node.parent:
            return False
        
        parent = node.parent
        if parent.type == 'method_definition' and parent.children[0] == node:
            return True
        
        return False
    
    def _get_parent(self, node):
        """Get parent node."""
        return node.parent if hasattr(node, 'parent') else None
    
    def _find_enclosing_scope(self, node):
        """Find the enclosing function/method scope."""
        current = node.parent
        while current:
            if current.type in ['function_declaration', 'method_definition', 'arrow_function', 'class_body']:
                return current
            current = current.parent
        return None
    
    def rename_variables(self, probability=0.5):
        """Randomly rename variables with given probability."""
        variables = self.find_variables_to_rename()
        
        # Create mapping for variables to rename
        for var in variables:
            if random.random() < probability:
                new_name = self.generate_random_name()
                self.variable_mappings[var['name']] = new_name
        
        # Apply the renaming
        if self.variable_mappings:
            return self.apply_renaming()
        
        return self.code_content
    
    def apply_renaming(self):
        """Apply the variable renaming to the code."""
        # Sort replacements by position (reverse order for proper byte handling)
        replacements = []
        
        def collect_identifiers(node):
            if node.type == 'identifier':
                text = self.code_content[node.start_byte:node.end_byte]
                if text in self.variable_mappings:
                    replacements.append({
                        'start': node.start_byte,
                        'end': node.end_byte,
                        'new_text': self.variable_mappings[text]
                    })
            
            for child in node.children:
                collect_identifiers(child)
        
        collect_identifiers(self.syntax_tree.root_node)
        
        # Sort by start position in reverse order to maintain byte positions
        replacements.sort(key=lambda x: x['start'], reverse=True)
        
        # Apply replacements
        new_code = self.code_content
        for replacement in replacements:
            new_code = (new_code[:replacement['start']] + 
                       replacement['new_text'] + 
                       new_code[replacement['end']:])
        
        return new_code

def demonstrate_transformation():
    """Demonstrate variable renaming on a sample."""
    test = read_jsonl('code_data/cleaned_data/test_200.jsonl')
    code_content = test[0]['text']
    
    # Also test with a more complex example
    complex_example = '''
import { Service } from './services';
import { DataProcessor } from './processors';

const MAX_RETRY_COUNT = 3;
const DEFAULT_TIMEOUT = 5000;

export class DataService {
  private service: Service;
  private processor: DataProcessor;
  
  constructor(service: Service, processor: DataProcessor) {
    this.service = service;
    this.processor = processor;
  }
  
  async processData(inputData: any[]): Promise<string[]> {
    const results: string[] = [];
    let currentAttempt = 0;
    
    for (const item of inputData) {
      try {
        const processed = await this.processor.process(item);
        const validated = this.validateData(processed);
        results.push(validated);
      } catch (error) {
        if (currentAttempt < MAX_RETRY_COUNT) {
          currentAttempt++;
          await this.delay(DEFAULT_TIMEOUT);
          continue;
        }
        throw error;
      }
    }
    
    return results;
  }
  
  private validateData(data: any): string {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid data format');
    }
    return JSON.stringify(data);
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
'''

    print("=== Testing with complex example ===")
    print("Original code:")
    print("-" * 40)
    print(complex_example)
    
    # Create variable renamer
    renamer = VariableRenamer(complex_example)
    
    # Rename variables
    transformed_code = renamer.rename_variables(probability=1.0)  # Always rename for demo
    
    print("\nTransformed code:")
    print("-" * 40)
    print(transformed_code)
    
    print("\nVariable mappings:")
    for old_name, new_name in renamer.variable_mappings.items():
        print(f"  {old_name} -> {new_name}")
    
    print(f"\nTotal variables renamed: {len(renamer.variable_mappings)}")
    
    print("\n=== Testing with original sample ===")
    print("Original code:")
    print("-" * 40)
    print(code_content)
    
    renamer2 = VariableRenamer(code_content)
    transformed2 = renamer2.rename_variables(probability=1.0)
    
    print("\nTransformed code:")
    print("-" * 40)
    print(transformed2)
    
    print("\nVariable mappings:")
    for old_name, new_name in renamer2.variable_mappings.items():
        print(f"  {old_name} -> {new_name}")
    
    print(f"\nTotal variables renamed: {len(renamer2.variable_mappings)}")

def process_dataset(input_file, output_file, probability=0.5):
    """Process entire dataset with variable renaming."""
    data = read_jsonl(input_file)
    
    augmented_data = []
    for item in data:
        original_code = item['text']
        
        # Create variable renamer and apply transformation
        renamer = VariableRenamer(original_code)
        transformed_code = renamer.rename_variables(probability)
        
        # Create new item with transformed code
        new_item = item.copy()
        new_item['text'] = transformed_code
        new_item['augmentation'] = 'variable_renaming'
        new_item['variable_mappings'] = renamer.variable_mappings
        
        augmented_data.append(new_item)
    
    # Write augmented data
    write_jsonl(output_file, augmented_data)
    print(f"Processed {len(augmented_data)} items. Output saved to {output_file}")

if __name__ == "__main__":
    # Demonstrate on sample
    demonstrate_transformation()
    
    # Process full dataset (uncomment to run)
    # process_dataset('code_data/cleaned_data/test_200.jsonl', 'code_data/augmented/variable_renamed.jsonl')
