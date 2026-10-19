import re
from typing import Any

from apps.tasks.models import Task
from apps.tasks.personalize import personalize_text

from .construct_guard import check_required_constructs
from .error_explainer import explain_execution_error, guidance_summary
from .judge0_client import Judge0Client, normalize_judge0_result


def _strip_output(text: str) -> str:
    return (text or '').replace('\r\n', '\n').rstrip('\n')


def _strip_input_prompts(stdout: str, source_code: str) -> str:
    text = stdout or ''
    for prompt in re.findall(r'input\s*\(\s*(["\'])(.*?)\1\s*\)', source_code or ''):
        text = text.replace(prompt[1], '', 1)
    return text


def _personalize_expected(text: str, user=None) -> str:
    if user is None or not text:
        return text or ''
    return personalize_text(text, user)


def check_stdout_exact(actual: str, expected: str, source_code: str = '') -> tuple[bool, str]:
    actual_norm = _strip_output(actual)
    expected_norm = _strip_output(expected)
    if source_code:
        actual_norm = _strip_output(_strip_input_prompts(actual, source_code))
    if actual_norm == expected_norm:
        return True, 'OK'
    return False, f'Ожидалось:\n{expected}\nПолучено:\n{actual}'


def check_stdout_regex(actual: str, pattern: str) -> tuple[bool, str]:
    if re.search(pattern, actual or '', re.MULTILINE | re.DOTALL):
        return True, 'OK'
    return False, f'Вывод не соответствует шаблону: {pattern}'


def _runtime_error_result(
    normalized: dict[str, Any],
    source_code: str,
    stdin: str = '',
    language_slug: str = 'python',
    *,
    is_trial_run: bool = False,
) -> dict[str, Any]:
    guidance = explain_execution_error(
        normalized.get('stderr', ''),
        normalized.get('compile_output', ''),
        source_code=source_code,
        stdin=stdin,
        language=language_slug,
        status=normalized['status'],
        is_trial_run=is_trial_run,
    )
    return {
        'accepted': False,
        'status': _map_run_status(normalized['status']),
        'message': guidance_summary(guidance),
        'error_guidance': guidance,
        'details': [normalized],
    }


def run_tests(
    client: Judge0Client,
    source_code: str,
    language_id: int,
    tests: list[dict[str, Any]],
    time_limit: float | None = None,
    memory_limit: int | None = None,
    language_slug: str = 'python',
    user=None,
) -> tuple[bool, list[dict[str, Any]]]:
    results = []
    for i, test in enumerate(tests):
        stdin = test.get('stdin', '')
        expected_stdout = _personalize_expected(test.get('expected_stdout', ''), user)
        pattern = _personalize_expected(test.get('pattern', ''), user) if test.get('pattern') else ''
        raw = client.run_code(source_code, language_id, stdin, time_limit, memory_limit)
        normalized = normalize_judge0_result(raw)
        passed = False
        message = ''
        guidance = None
        if normalized['status'] != 'success':
            guidance = explain_execution_error(
                normalized.get('stderr', ''),
                normalized.get('compile_output', ''),
                source_code=source_code,
                stdin=stdin,
                language=language_slug,
                status=normalized['status'],
                is_trial_run=False,
            )
            message = guidance_summary(guidance)
        elif 'expected_stdout' in test:
            passed, message = check_stdout_exact(
                normalized['stdout'], expected_stdout, source_code,
            )
        elif 'pattern' in test:
            passed, message = check_stdout_regex(normalized['stdout'], pattern)
        result_item = {
            'index': i,
            'passed': passed,
            'message': message,
            'stdout': normalized['stdout'],
            'stderr': normalized['stderr'],
            'hidden': test.get('hidden', False),
        }
        if guidance is not None:
            result_item['error_guidance'] = guidance
        results.append(result_item)
        if not passed:
            return False, results
    return True, results


def evaluate_submission(task: Task, source_code: str, user=None) -> dict[str, Any]:
    from apps.submissions.starter_guard import should_reject_unchanged_starter

    if should_reject_unchanged_starter(task, source_code, user):
        return {
            'accepted': False,
            'status': 'wrong_answer',
            'message': 'Сначала измени код задания. Нельзя сдавать стартовый код без изменений.',
            'details': [],
            'unchanged_starter': True,
        }

    construct_error = check_required_constructs(source_code, task.checker_config_json or {})
    if construct_error:
        return {
            'accepted': False,
            'status': 'wrong_answer',
            'message': construct_error,
            'details': [],
            'missing_constructs': True,
        }

    client = Judge0Client()
    language = task.language
    time_limit = language.default_time_limit
    memory_limit = language.default_memory_limit

    if task.checker_type == Task.CheckerType.MANUAL:
        return {
            'accepted': False,
            'status': 'manual_review',
            'message': 'Решение отправлено на ручную проверку.',
            'details': [],
        }

    language_slug = language.slug
    expected_stdout = _personalize_expected(task.expected_stdout or '', user)

    if task.checker_type == Task.CheckerType.STDOUT_EXACT:
        raw = client.run_code(source_code, language.judge0_language_id, task.stdin, time_limit, memory_limit)
        normalized = normalize_judge0_result(raw)
        if normalized['status'] != 'success':
            return _runtime_error_result(
                normalized,
                source_code,
                task.stdin,
                language_slug,
            )
        passed, msg = check_stdout_exact(normalized['stdout'], expected_stdout, source_code)
        result: dict[str, Any] = {
            'accepted': passed,
            'status': 'accepted' if passed else 'wrong_answer',
            'message': 'Отлично! Программа работает.' if passed else msg,
            'details': [normalized],
        }
        if not passed:
            result['expected'] = expected_stdout
            result['got'] = _strip_output(_strip_input_prompts(normalized['stdout'], source_code))
            result['is_hidden'] = False
        return result

    if task.checker_type == Task.CheckerType.STDOUT_REGEX:
        raw = client.run_code(source_code, language.judge0_language_id, task.stdin, time_limit, memory_limit)
        normalized = normalize_judge0_result(raw)
        if normalized['status'] != 'success':
            return _runtime_error_result(
                normalized,
                source_code,
                task.stdin,
                language_slug,
            )
        pattern = (task.checker_config_json or {}).get('pattern', task.expected_stdout)
        pattern = _personalize_expected(pattern or '', user)
        passed, msg = check_stdout_regex(normalized['stdout'], pattern)
        result = {
            'accepted': passed,
            'status': 'accepted' if passed else 'wrong_answer',
            'message': 'Отлично! Программа работает.' if passed else msg,
            'details': [normalized],
        }
        if not passed:
            result['expected'] = pattern
            result['got'] = _strip_output(normalized['stdout'])
            result['is_hidden'] = False
        return result

    tests = list(task.visible_tests_json or [])
    tests += list(task.hidden_tests_json or [])
    for tc in task.test_cases.all():
        tests.append({
            'stdin': tc.stdin,
            'expected_stdout': tc.expected_stdout,
            'hidden': tc.is_hidden,
        })
    if not tests and task.stdin:
        tests = [{'stdin': task.stdin, 'expected_stdout': task.expected_stdout}]

    if not tests:
        return {
            'accepted': False,
            'status': 'wrong_answer',
            'message': 'Нет тестов для проверки.',
            'details': [],
        }

    passed, details = run_tests(
        client,
        source_code,
        language.judge0_language_id,
        tests,
        time_limit,
        memory_limit,
        language_slug,
        user=user,
    )
    result = {
        'accepted': passed,
        'status': 'accepted' if passed else 'wrong_answer',
        'message': 'Отлично! Программа работает.' if passed else details[-1].get('message', 'Неверный ответ'),
        'details': details,
    }
    if not passed:
        result.update(_failure_feedback(task, details, source_code, user=user))
        failed = details[-1] if details else {}
        if failed.get('error_guidance'):
            result['error_guidance'] = failed['error_guidance']
    return result


def _failure_feedback(
    task: Task,
    details: list[dict[str, Any]],
    source_code: str = '',
    user=None,
) -> dict[str, Any]:
    visible = list(task.visible_tests_json or [])
    for detail in details:
        if detail.get('passed'):
            continue
        idx = detail.get('index', 0)
        is_hidden = bool(detail.get('hidden')) or idx >= len(visible)
        feedback: dict[str, Any] = {
            'failed_test_index': idx,
            'is_hidden': is_hidden,
        }
        if not is_hidden and idx < len(visible):
            test = visible[idx]
            if isinstance(test, dict) and 'expected_stdout' in test:
                feedback['expected'] = _personalize_expected(test.get('expected_stdout', ''), user)
                raw_stdout = detail.get('stdout', '')
                feedback['got'] = _strip_output(_strip_input_prompts(raw_stdout, source_code))
        return feedback
    return {}


def _map_run_status(run_status: str) -> str:
    mapping = {
        'success': 'accepted',
        'compile_error': 'compile_error',
        'timeout': 'time_limit',
        'error': 'runtime_error',
    }
    return mapping.get(run_status, 'runtime_error')
