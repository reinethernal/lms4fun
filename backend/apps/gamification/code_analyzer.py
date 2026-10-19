import re
from typing import Any


def _count_pattern(code: str, pattern: str) -> int:
    return len(re.findall(pattern, code, re.MULTILINE | re.IGNORECASE))


def analyze_code(source_code: str, language_slug: str) -> dict[str, Any]:
    code = source_code or ''
    slug = (language_slug or 'python').lower()
    skills: dict[str, int] = {}

    if slug == 'python':
        skills['input_used'] = 1 if re.search(r'\binput\s*\(', code) else 0
        skills['if_else_used'] = 1 if re.search(r'\bif\b', code) and re.search(r'\belse\b', code) else 0
        skills['elif_used'] = _count_pattern(code, r'\belif\b')
        skills['logical_and_used'] = _count_pattern(code, r'\band\b')
        skills['logical_or_used'] = _count_pattern(code, r'\bor\b')
        skills['while_used'] = 1 if re.search(r'\bwhile\b', code) else 0
        skills['for_used'] = 1 if re.search(r'\bfor\b', code) else 0
        skills['break_used'] = 1 if re.search(r'\bbreak\b', code) else 0
        skills['random_used'] = 1 if re.search(r'\brandom\b', code) else 0
        skills['append_used'] = 1 if re.search(r'\.append\s*\(', code) else 0
        skills['remove_used'] = 1 if re.search(r'\.remove\s*\(', code) else 0
        skills['in_operator_used'] = 1 if re.search(r'\bin\b', code) else 0
        skills['list_created'] = 1 if re.search(r'\[', code) else 0
        skills['functions_created'] = _count_pattern(code, r'^\s*def\s+\w+', )
        skills['function_parameters_used'] = 1 if re.search(r'def\s+\w+\s*\([^)]+\)', code) else 0
        skills['return_used'] = 1 if re.search(r'\breturn\b', code) else 0
        skills['try_except_used'] = 1 if re.search(r'\btry\b', code) and re.search(r'\bexcept\b', code) else 0
        skills['comment_added'] = _count_pattern(code, r'^\s*#')
        skills['arithmetic_plus_used'] = 1 if '+' in code else 0
        skills['arithmetic_mul_used'] = 1 if '*' in code else 0
        skills['print_used'] = 1 if re.search(r'\bprint\s*\(', code) else 0
        skills['string_tasks'] = 1 if re.search(r'["\']', code) else 0
        skills['numbers_tasks'] = 1 if re.search(r'\b\d+\b', code) else 0
        skills['variables_used'] = len(re.findall(r'^\s*[a-zA-Z_]\w*\s*=', code, re.MULTILINE))
        skills['custom_changes_added'] = 1 if code.strip() else 0
        blank_lines = len(re.findall(r'^\s*$', code, re.MULTILINE))
        total_lines = max(1, len(code.splitlines()))
        skills['clean_code_score'] = 1 if blank_lines <= total_lines * 0.3 else 0
    elif slug == 'javascript':
        skills['js_console_log_success'] = 1 if re.search(r'console\.log\s*\(', code) else 0
        skills['print_used'] = skills['js_console_log_success']
    elif slug == 'java':
        skills['java_compiles_success'] = 1 if re.search(r'public\s+class', code) else 0
        skills['print_used'] = 1 if re.search(r'System\.out\.print', code) else 0

    return {'skills': skills}


def merge_skill_stats(existing: dict, analysis: dict) -> dict:
    skills = dict(existing.get('skills', {}))
    for key, value in analysis.get('skills', {}).items():
        if isinstance(value, bool):
            value = 1 if value else 0
        skills[key] = skills.get(key, 0) + int(value)
    existing['skills'] = skills
    return existing


def detect_error_types(stderr: str, compile_output: str) -> list[str]:
    text = f'{stderr}\n{compile_output}'.lower()
    patterns = [
        ('syntax_error', 'syntaxerror'),
        ('indentation_error', 'indentationerror'),
        ('indentation_error', 'taberror'),
        ('name_error', 'nameerror'),
        ('eof_error', 'eoferror'),
        ('value_error', 'valueerror'),
        ('type_error', 'typeerror'),
        ('index_error', 'indexerror'),
        ('key_error', 'keyerror'),
        ('zero_division_error', 'zerodivisionerror'),
        ('attribute_error', 'attributeerror'),
        ('import_error', 'importerror'),
        ('import_error', 'modulenotfounderror'),
        ('recursion_error', 'recursionerror'),
    ]
    found = []
    for error_type, pattern in patterns:
        if pattern in text and error_type not in found:
            found.append(error_type)
    return found
