import re
from typing import Any


def _count_input_calls(source_code: str) -> int:
    return len(re.findall(r'\binput\s*\(', source_code or ''))


def _stdin_line_count(stdin: str) -> int:
    if not stdin or not stdin.strip():
        return 0
    normalized = stdin.replace('\r\n', '\n').rstrip('\n')
    if not normalized:
        return 0
    return len(normalized.split('\n'))


def _parse_traceback_line(text: str) -> int | None:
    match = re.search(r'File\s+"[^"]+",\s+line\s+(\d+)', text)
    if match:
        return int(match.group(1))
    return None


def _parse_error_name(text: str) -> str | None:
    for line in reversed((text or '').strip().splitlines()):
        match = re.match(r'^(\w+(?:Error|Exception)):\s*(.*)$', line.strip())
        if match:
            return match.group(1)
    return None


def _eof_why_text(*, is_trial_run: bool) -> str:
    if is_trial_run:
        return (
            'Каждый вызов input() — отдельный вопрос: программа останавливается '
            'и ждёт одну строку ответа. Ответ на первый вопрос не подставляется во второй. '
            'На платформе ответ вводят в терминале на строке с префиксом > и нажимают Enter. '
            'Если строк меньше, чем вызовов input(), Python завершает программу с EOFError.'
        )
    return (
        'При сдаче платформа передаёт программе готовый тестовый ввод — по одной строке '
        'на каждый ожидаемый input(). Если в коде больше вызовов input(), чем строк в тесте, '
        'очередной input() не получает данных и возникает EOFError.'
    )


def _eof_error_guidance(source_code: str, stdin: str, *, is_trial_run: bool) -> dict[str, Any]:
    input_count = _count_input_calls(source_code)
    stdin_lines = _stdin_line_count(stdin)
    why = _eof_why_text(is_trial_run=is_trial_run)

    if input_count > 1 and stdin_lines < input_count:
        summary = (
            f'Программе нужно {input_count} ответа (по одному на каждый input()), '
            f'а получено только {stdin_lines}.'
        )
        attention = [
            'Посмотри на последний вопрос в выводе — на него ещё нет ответа.',
            'Введи следующий ответ на строке > и нажми Enter '
            '(каждый input() ждёт свою строку).',
            'Если лишний input() не нужен по заданию — убери его из кода.',
        ]
        if not is_trial_run:
            attention = [
                f'В коде {input_count} вызова input(), а тест даёт меньше строк ввода.',
                'Оставь только те input(), которые требует задание.',
                'Каждый input() читает ровно одну строку.',
            ]
    elif is_trial_run and not stdin.strip():
        summary = 'Программа вызвала input(), но ответ в терминале ещё не введён.'
        attention = [
            'Напиши ответ на строке > в терминале и нажми Enter.',
            'Если вопросов несколько — отвечай по очереди: каждый input() ждёт свою строку.',
            'При сдаче задания ввод подставляется автоматически из автотестов.',
        ]
    elif is_trial_run:
        summary = 'Программа вызвала input(), но данных для чтения не хватило.'
        attention = [
            'Проверь, что в терминале достаточно ответов для всех input().',
            'Каждый input() читает одну строку до Enter.',
            'Если добавил лишний input() — убери его или ответь ещё раз на строке >.',
        ]
    else:
        summary = 'При проверке не хватило строк ввода для всех input() в программе.'
        attention = [
            'Сравни число input() в коде с тем, сколько ответов реально нужно по заданию.',
            'Убери лишние input(), если задание их не требует.',
            'Каждый input() читает ровно одну строку.',
        ]

    return {
        'error_type': 'eof_error',
        'title': 'Не хватает данных для ввода',
        'summary': summary,
        'why': why,
        'attention': attention,
    }


def _build_guidance(
    error_type: str,
    title: str,
    summary: str,
    attention: list[str],
    *,
    line: int | None = None,
    raw: str = '',
    why: str = '',
) -> dict[str, Any]:
    result: dict[str, Any] = {
        'error_type': error_type,
        'title': title,
        'summary': summary,
        'attention': attention,
        'raw': raw,
    }
    if line is not None:
        result['line'] = line
    if why:
        result['why'] = why
    return result


def _explain_python_error(
    text: str,
    *,
    source_code: str = '',
    stdin: str = '',
    is_trial_run: bool = True,
) -> dict[str, Any]:
    line = _parse_traceback_line(text)
    error_name = _parse_error_name(text)
    lower = text.lower()

    if error_name == 'EOFError' or 'eoferror' in lower:
        guidance = _eof_error_guidance(source_code, stdin, is_trial_run=is_trial_run)
        guidance['line'] = line
        guidance['raw'] = text
        return guidance

    if error_name == 'SyntaxError' or 'syntaxerror' in lower:
        return _build_guidance(
            'syntax_error',
            'Синтаксическая ошибка',
            'Python не смог разобрать код — где-то нарушены правила языка.',
            [
                'Проверь двоеточие после if, for, while, def и else.',
                'Проверь, что все скобки (), [] и кавычки " " закрыты.',
                'Посмотри на строку из сообщения об ошибке — там часто указано место.',
            ],
            line=line,
            raw=text,
        )

    if error_name in ('IndentationError', 'TabError') or 'indentationerror' in lower or 'taberror' in lower:
        return _build_guidance(
            'indentation_error',
            'Ошибка отступов',
            'Строки внутри if, for, while или def должны быть сдвинуты вправо.',
            [
                'После двоеточия (:) следующая строка должна начинаться с отступа (обычно 4 пробела).',
                'Не смешивай табы и пробелы — используй только пробелы.',
                'Все строки одного блока должны иметь одинаковый отступ.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'NameError' or 'nameerror' in lower:
        name_match = re.search(r"name '(\w+)' is not defined", text)
        var_name = name_match.group(1) if name_match else 'переменная'
        return _build_guidance(
            'name_error',
            'Неизвестное имя',
            f'Python не знает имя «{var_name}» — переменная не объявлена или опечатка.',
            [
                f'Объяви переменную до использования: {var_name} = ...',
                'Проверь написание имени — Python различает большие и маленькие буквы.',
                'Если это функция — проверь, что def написан выше вызова.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'TypeError' or 'typeerror' in lower:
        return _build_guidance(
            'type_error',
            'Неверный тип данных',
            'Операция применена к данным неподходящего типа.',
            [
                'Нельзя складывать строку и число без преобразования: int() или str().',
                'Проверь, что в input() результат преобразован, если нужно число: int(input()).',
                'Убедись, что функция получает аргументы правильного типа.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'ValueError' or 'valueerror' in lower:
        return _build_guidance(
            'value_error',
            'Неверное значение',
            'Тип данных подходит, но значение нельзя использовать так, как ты ожидаешь.',
            [
                'int("abc") не работает — строка должна содержать число.',
                'Проверь, что пользователь вводит данные в правильном формате.',
                'Можно обработать ошибку через try/except ValueError.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'IndexError' or 'indexerror' in lower:
        return _build_guidance(
            'index_error',
            'Индекс за пределами списка',
            'Обращение к элементу списка по номеру, которого не существует.',
            [
                'Индексы начинаются с 0: первый элемент — list[0].',
                'Проверь длину списка: len(my_list) — последний индекс len(my_list) - 1.',
                'Убедись, что список не пустой перед обращением к элементу.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'KeyError' or 'keyerror' in lower:
        return _build_guidance(
            'key_error',
            'Ключ не найден в словаре',
            'Словарь не содержит запрашиваемого ключа.',
            [
                'Проверь правильность написания ключа.',
                'Используй dict.get("ключ", значение_по_умолчанию) для безопасного доступа.',
                'Убедись, что ключ добавлен в словарь до обращения.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'ZeroDivisionError' or 'zerodivisionerror' in lower:
        return _build_guidance(
            'zero_division_error',
            'Деление на ноль',
            'Программа пытается разделить число на ноль.',
            [
                'Проверь, что делитель не равен 0 перед операцией деления.',
                'Добавь проверку: if b != 0: ...',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'AttributeError' or 'attributeerror' in lower:
        return _build_guidance(
            'attribute_error',
            'Атрибут не найден',
            'Объект не имеет запрашиваемого метода или свойства.',
            [
                'Проверь тип переменной — возможно, это не тот объект, который ты ожидаешь.',
                'Убедись, что имя метода написано правильно.',
                'Списки используют .append(), строки — .upper(), .lower() и т.д.',
            ],
            line=line,
            raw=text,
        )

    if error_name in ('ImportError', 'ModuleNotFoundError') or 'modulenotfounderror' in lower or 'importerror' in lower:
        return _build_guidance(
            'import_error',
            'Модуль не найден',
            'Python не смог найти или импортировать модуль.',
            [
                'Проверь написание: import random, import math.',
                'Убедись, что модуль существует и доступен в этой среде.',
            ],
            line=line,
            raw=text,
        )

    if error_name == 'RecursionError' or 'recursionerror' in lower or 'maximum recursion depth' in lower:
        return _build_guidance(
            'recursion_error',
            'Слишком глубокая рекурсия',
            'Функция вызывает сама себя слишком много раз — возможно, нет условия выхода.',
            [
                'Добавь базовый случай (условие, при котором функция перестаёт вызывать себя).',
                'Проверь, что return есть во всех ветках рекурсивной функции.',
            ],
            line=line,
            raw=text,
        )

    return _build_guidance(
        'generic_runtime',
        'Ошибка выполнения',
        'Программа завершилась с ошибкой во время работы.',
        [
            'Прочитай последнюю строку сообщения об ошибке — там тип и описание.',
            'Найди номер строки в traceback и проверь код на этой строке.',
            'Исправь одну ошибку и запусти программу снова.',
        ],
        line=line,
        raw=text,
    )


def is_waiting_for_input(
    *,
    source_code: str,
    stdin: str = '',
    run_status: str = 'error',
    stderr: str = '',
) -> bool:
    """True when EOF means the program is paused mid-dialogue, not a student mistake."""
    if run_status == 'success':
        return False
    text = (stderr or '').lower()
    if 'eoferror' not in text and 'eof when reading a line' not in text:
        return False
    input_count = _count_input_calls(source_code)
    if input_count == 0:
        return False
    return _stdin_line_count(stdin) < input_count


def explain_stdin_validation(source_code: str, stdin: str = '') -> dict[str, Any] | None:
    """Return guidance when trial run stdin is missing or insufficient for input() calls."""
    input_count = _count_input_calls(source_code)
    if input_count == 0:
        return None
    stdin_lines = _stdin_line_count(stdin)
    if not stdin.strip() or stdin_lines < input_count:
        guidance = _eof_error_guidance(source_code, stdin, is_trial_run=True)
        guidance['raw'] = ''
        return guidance
    return None


def explain_execution_error(
    stderr: str = '',
    compile_output: str = '',
    *,
    source_code: str = '',
    stdin: str = '',
    language: str = 'python',
    status: str = 'error',
    is_trial_run: bool = True,
) -> dict[str, Any] | None:
    """Return student-friendly error guidance or None if no error."""
    if status == 'success':
        return None

    if status == 'timeout':
        return _build_guidance(
            'timeout',
            'Превышено время выполнения',
            'Программа работала слишком долго и была остановлена.',
            [
                'Проверь, нет ли бесконечного цикла while True без break.',
                'Убедись, что цикл for имеет условие завершения.',
                'Возможно, программа выполняет слишком много повторений.',
            ],
            raw=stderr or compile_output,
        )

    if compile_output and compile_output.strip():
        return _build_guidance(
            'compile_error',
            'Ошибка компиляции',
            'Код не удалось скомпилировать перед запуском.',
            [
                'Проверь синтаксис: скобки, точки с запятой (в Java), объявление класса.',
                'Прочитай сообщение компилятора — там указана строка с ошибкой.',
                'Убедись, что все импорты и имена классов написаны правильно.',
            ],
            raw=compile_output,
        )

    text = (stderr or '').strip()
    if not text:
        return _build_guidance(
            'generic_runtime',
            'Ошибка выполнения',
            'Программа завершилась с ошибкой.',
            [
                'Попробуй запустить программу ещё раз.',
                'Проверь код на опечатки и логические ошибки.',
            ],
            raw=text,
        )

    slug = (language or 'python').lower()
    if slug == 'python':
        return _explain_python_error(
            text,
            source_code=source_code,
            stdin=stdin,
            is_trial_run=is_trial_run,
        )

    return _build_guidance(
        'generic_runtime',
        'Ошибка выполнения',
        'Программа завершилась с ошибкой во время работы.',
        [
            'Прочитай сообщение об ошибке — там указана причина.',
            'Найди строку с ошибкой и проверь код.',
        ],
        line=_parse_traceback_line(text),
        raw=text,
    )


def guidance_summary(guidance: dict[str, Any] | None) -> str:
    if not guidance:
        return 'Ошибка выполнения'
    return guidance.get('summary') or guidance.get('title') or 'Ошибка выполнения'
