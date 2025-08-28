import os
import random
import string
import json
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import *
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_typescript as tst
from openai import OpenAI

# Initialize tree-sitter for ArkTS/TypeScript
TS_LANGUAGE = Language(tst.language_typescript())
parser = Parser()
parser.language = TS_LANGUAGE


def _random_name(name: str) -> str:
    """Generate a random variable name."""
    num_digits = random.randint(1, 3)
    random_digits = ''.join(random.choice(string.digits) for _ in range(num_digits))
    return name + random_digits


def _llm_synonym(names: list[str], model: str = "<Model>", prompt_path: str | None = None) -> list[str]:
    """Return synonyms for variable names using an LLM. Fallback to random names if the
    request fails."""
    # Prepare the prompt
    prompt_template = "Generate semantically similar variable names for the following list. Consider coding conventions and context. Output ONLY a JSON array with the new names in the same order. No other text, no markdown formatting."
    if prompt_path and os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    
    # Format the variable names list in the prompt
    names_str = ", ".join(names)
    message = f"{prompt_template}\n\nVariable names: [{names_str}]"

    try:
        client = OpenAI(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            response_format={"type": "json_object"}
        )
        response = completion.choices[0].message.content.strip()
        
        # Try to parse the response as JSON
        try:
            result = json.loads(response)
            if isinstance(result, list) and len(result) == len(names):
                # Clean each name
                cleaned_results = []
                for name, i in enumerate(result):
                    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(name))
                    if cleaned and cleaned[0].isdigit():
                        cleaned = f"_{cleaned}"
                    cleaned_results.append(cleaned or _random_name(names[i]))
                return cleaned_results
            else:
                # Fall back to individual processing if list format is wrong
                return [_random_name(name) for name in names]
        except json.JSONDecodeError:
            # Fall back to individual processing if JSON parsing fails
            return [_random_name(name) for name in names]
    except Exception as exc:
        print(f"LLM request failed for names {names}: {exc}")
        return [_random_name(name) for name in names]


def _collect_variable_identifiers(tree, code: str):
    """Return a mapping of variable names to their identifier nodes."""
    query = Query(TS_LANGUAGE, "(variable_declarator name: (identifier) @var)")
    cursor = QueryCursor(query)
    capture_dict = cursor.captures(tree.root_node)
    variables = {}
    for node in capture_dict.get('var', []):
        name = code[node.start_byte:node.end_byte]
        variables.setdefault(name, []).append(node)
    return variables


def _collect_all_identifiers(tree):
    """Collect all identifier nodes in the tree."""
    query = Query(TS_LANGUAGE, "(identifier) @id")
    cursor = QueryCursor(query)
    capture_dict = cursor.captures(tree.root_node)
    return capture_dict.get('id', [])


def rename_variables(
    code: str,
    max_changes: int = 2,
    *,
    use_llm: bool = False,
    model: str = "<Model>",
    prompt_path: str | None = None,
) -> str:
    """Randomly rename up to `max_changes` variables in the given ArkTS code.

    When ``use_llm`` is True, try generating synonyms for the selected variable
    names using the provided LLM model and prompt template."""
    tree = parser.parse(code.encode("utf-8"))
    variables = _collect_variable_identifiers(tree, code)
    if not variables:
        return code

    num_changes = random.randint(1, min(max_changes, len(variables)))
    selected = random.sample(list(variables.keys()), num_changes)
    mapping = {}
    
    if use_llm and selected:
        # Use LLM to generate synonyms for all selected names at once
        new_names = _llm_synonym(selected, model=model, prompt_path=prompt_path)
        mapping = dict(zip(selected, new_names))
    else:
        # Use random names
        for name in selected:
            mapping[name] = _random_name(name)

    id_nodes = _collect_all_identifiers(tree)
    replacements = []
    for node in id_nodes:
        text = code[node.start_byte:node.end_byte]
        if text in mapping:
            parent = node.parent
            if parent and parent.type in ['property_identifier', 'shorthand_property_identifier']:
                continue
            replacements.append((node.start_byte, node.end_byte, mapping[text]))

    replacements.sort(key=lambda x: x[0], reverse=True)
    new_code = code
    for start, end, new_text in replacements:
        new_code = new_code[:start] + new_text + new_code[end:]
    return new_code


def get_variable_synonyms(
    names: list[str],
    *,
    model: str = "<Model>",
    prompt_path: str | None = None,
) -> list[str]:
    """Get synonyms for a list of variable names using LLM and return as JSON list.
    
    This function is specifically designed for generating synonyms for multiple 
    variable names at once and returning them in a JSON list format."""
    return _llm_synonym(names, model=model, prompt_path=prompt_path)


if __name__ == "__main__":
    # example = """
    # const test = 1;
    # function demo() {
    #     let value = test + 2;
    #     return value;
    # }
    # """
    # print("Random rename:")
    # print(rename_variables(example))

    # print("\nLLM rename (may fallback to random if request fails):")
    prompt_file = os.path.join(os.path.dirname(__file__), "..", "prompt_templates", "variable_synonym_prompt.txt")
    # print(rename_variables(example, use_llm=True, prompt_path=prompt_file, model="deepseek-v3-250324"))
    
    # # Test the new function for getting synonyms for multiple names
    # print("\nMultiple variable synonyms:")
    # test_names = ["userCount", "isActive", "fileName"]
    # synonyms = get_variable_synonyms(test_names, prompt_path=prompt_file, model="deepseek-v3-250324")
    # print(json.dumps(dict(zip(test_names, synonyms)), indent=2))
    test200 = read_jsonl("./code_data/cleaned_data/test_200.jsonl")
    for item in test200[:4]:
        print("="*50)
        print("Before transform:")
        print(item['text'])
        item['text'] = rename_variables(item['text'], use_llm=True, prompt_path=prompt_file, model="qwen3-coder-plus")
        print("After transform:")
        print(item['text'])
        