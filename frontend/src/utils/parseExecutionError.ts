import type { ErrorGuidance } from './errorGuidance';

const INPUT_CALL_RE = /\binput\s*\(/g;

export function countInputCalls(code: string): number {
  return (code.match(INPUT_CALL_RE) ?? []).length;
}

export function stdinLineCount(stdin: string): number {
  if (!stdin || !stdin.trim()) return 0;
  const normalized = stdin.replace(/\r\n/g, '\n').replace(/\n+$/, '');
  if (!normalized) return 0;
  return normalized.split('\n').length;
}

const EOF_WHY_TRIAL =
  'Каждый вызов input() — отдельный вопрос: программа останавливается '
  + 'и ждёт одну строку ответа. Ответ на первый вопрос не подставляется во второй. '
  + 'На платформе ответ вводят в терминале на строке с префиксом > и нажимают Enter. '
  + 'Если строк меньше, чем вызовов input(), Python завершает программу с EOFError.';

function buildEofGuidance(
  sourceCode: string,
  stdin: string,
  raw = '',
  line?: number,
): ErrorGuidance {
  const inputCount = countInputCalls(sourceCode);
  const lines = stdinLineCount(stdin);

  if (inputCount > 1 && lines < inputCount) {
    return {
      error_type: 'eof_error',
      title: 'Не хватает данных для ввода',
      summary:
        `Программе нужно ${inputCount} ответа (по одному на каждый input()), `
        + `а получено только ${lines}.`,
      why: EOF_WHY_TRIAL,
      attention: [
        'Посмотри на последний вопрос в выводе — на него ещё нет ответа.',
        'Введи следующий ответ на строке > и нажми Enter '
        + '(каждый input() ждёт свою строку).',
        'Если лишний input() не нужен по заданию — убери его из кода.',
      ],
      raw,
      ...(line !== undefined ? { line } : {}),
    };
  }

  if (!stdin.trim()) {
    return {
      error_type: 'eof_error',
      title: 'Не хватает данных для ввода',
      summary: 'Программа вызвала input(), но ответ в терминале ещё не введён.',
      why: EOF_WHY_TRIAL,
      attention: [
        'Напиши ответ на строке > в терминале и нажми Enter.',
        'Если вопросов несколько — отвечай по очереди: каждый input() ждёт свою строку.',
        'При сдаче задания ввод подставляется автоматически из автотестов.',
      ],
      raw,
      ...(line !== undefined ? { line } : {}),
    };
  }

  return {
    error_type: 'eof_error',
    title: 'Не хватает данных для ввода',
    summary: 'Программа вызвала input(), но данных для чтения не хватило.',
    why: EOF_WHY_TRIAL,
    attention: [
      'Проверь, что в терминале достаточно ответов для всех input().',
      'Каждый input() читает одну строку до Enter.',
      'Если добавил лишний input() — убери его или ответь ещё раз на строке >.',
    ],
    raw,
    ...(line !== undefined ? { line } : {}),
  };
}

export function validateStdinForInput(code: string, stdin: string): ErrorGuidance | null {
  const inputCount = countInputCalls(code);
  if (inputCount === 0) return null;

  const lines = stdinLineCount(stdin);
  if (!stdin.trim() || lines < inputCount) {
    return buildEofGuidance(code, stdin);
  }

  return null;
}

function parseTracebackLine(text: string): number | undefined {
  const match = text.match(/File\s+"[^"]+",\s+line\s+(\d+)/);
  return match ? Number(match[1]) : undefined;
}

function buildGuidance(
  errorType: string,
  title: string,
  summary: string,
  attention: string[],
  raw: string,
  line?: number,
  why?: string,
): ErrorGuidance {
  return {
    error_type: errorType,
    title,
    summary,
    attention,
    raw,
    ...(why ? { why } : {}),
    ...(line !== undefined ? { line } : {}),
  };
}

function explainPythonStderr(stderr: string, sourceCode: string, stdin: string): ErrorGuidance {
  const lower = stderr.toLowerCase();
  const line = parseTracebackLine(stderr);

  if (lower.includes('eoferror')) {
    return buildEofGuidance(sourceCode, stdin, stderr, line);
  }

  if (lower.includes('syntaxerror')) {
    return buildGuidance(
      'syntax_error',
      'Синтаксическая ошибка',
      'Python не смог разобрать код — где-то нарушены правила языка.',
      [
        'Проверь двоеточие после if, for, while, def и else.',
        'Проверь, что все скобки (), [] и кавычки " " закрыты.',
        'Посмотри на строку из сообщения об ошибке — там часто указано место.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('indentationerror') || lower.includes('taberror')) {
    return buildGuidance(
      'indentation_error',
      'Ошибка отступов',
      'Строки внутри if, for, while или def должны быть сдвинуты вправо.',
      [
        'После двоеточия (:) следующая строка должна начинаться с отступа (обычно 4 пробела).',
        'Не смешивай табы и пробелы — используй только пробелы.',
        'Все строки одного блока должны иметь одинаковый отступ.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('nameerror')) {
    const nameMatch = stderr.match(/name '(\w+)' is not defined/i);
    const varName = nameMatch?.[1] ?? 'переменная';
    return buildGuidance(
      'name_error',
      'Неизвестное имя',
      `Python не знает имя «${varName}» — переменная не объявлена или опечатка.`,
      [
        `Объяви переменную до использования: ${varName} = ...`,
        'Проверь написание имени — Python различает большие и маленькие буквы.',
        'Если это функция — проверь, что def написан выше вызова.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('typeerror')) {
    return buildGuidance(
      'type_error',
      'Неверный тип данных',
      'Операция применена к данным неподходящего типа.',
      [
        'Нельзя складывать строку и число без преобразования: int() или str().',
        'Проверь, что в input() результат преобразован, если нужно число: int(input()).',
        'Убедись, что функция получает аргументы правильного типа.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('valueerror')) {
    return buildGuidance(
      'value_error',
      'Неверное значение',
      'Тип данных подходит, но значение нельзя использовать так, как ты ожидаешь.',
      [
        'int("abc") не работает — строка должна содержать число.',
        'Проверь, что пользователь вводит данные в правильном формате.',
        'Можно обработать ошибку через try/except ValueError.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('indexerror')) {
    return buildGuidance(
      'index_error',
      'Индекс за пределами списка',
      'Обращение к элементу списка по номеру, которого не существует.',
      [
        'Индексы начинаются с 0: первый элемент — list[0].',
        'Проверь длину списка: len(my_list) — последний индекс len(my_list) - 1.',
        'Убедись, что список не пустой перед обращением к элементу.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('keyerror')) {
    return buildGuidance(
      'key_error',
      'Ключ не найден в словаре',
      'Словарь не содержит запрашиваемого ключа.',
      [
        'Проверь правильность написания ключа.',
        'Используй dict.get("ключ", значение_по_умолчанию) для безопасного доступа.',
        'Убедись, что ключ добавлен в словарь до обращения.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('zerodivisionerror')) {
    return buildGuidance(
      'zero_division_error',
      'Деление на ноль',
      'Программа пытается разделить число на ноль.',
      [
        'Проверь, что делитель не равен 0 перед операцией деления.',
        'Добавь проверку: if b != 0: ...',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('attributeerror')) {
    return buildGuidance(
      'attribute_error',
      'Атрибут не найден',
      'Объект не имеет запрашиваемого метода или свойства.',
      [
        'Проверь тип переменной — возможно, это не тот объект, который ты ожидаешь.',
        'Убедись, что имя метода написано правильно.',
        'Списки используют .append(), строки — .upper(), .lower() и т.д.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('importerror') || lower.includes('modulenotfounderror')) {
    return buildGuidance(
      'import_error',
      'Модуль не найден',
      'Python не смог найти или импортировать модуль.',
      [
        'Проверь написание: import random, import math.',
        'Убедись, что модуль существует и доступен в этой среде.',
      ],
      stderr,
      line,
    );
  }

  if (lower.includes('recursionerror') || lower.includes('maximum recursion depth')) {
    return buildGuidance(
      'recursion_error',
      'Слишком глубокая рекурсия',
      'Функция вызывает сама себя слишком много раз — возможно, нет условия выхода.',
      [
        'Добавь базовый случай (условие, при котором функция перестаёт вызывать себя).',
        'Проверь, что return есть во всех ветках рекурсивной функции.',
      ],
      stderr,
      line,
    );
  }

  return buildGuidance(
    'generic_runtime',
    'Ошибка выполнения',
    'Программа завершилась с ошибкой во время работы.',
    [
      'Прочитай последнюю строку сообщения об ошибке — там тип и описание.',
      'Найди номер строки в traceback и проверь код на этой строке.',
      'Исправь одну ошибку и запусти программу снова.',
    ],
    stderr,
    line,
  );
}

export function parseExecutionError(options: {
  stderr?: string;
  compileOutput?: string;
  status?: string;
  sourceCode?: string;
  stdin?: string;
}): ErrorGuidance | null {
  const { stderr = '', compileOutput = '', status = '', sourceCode = '', stdin = '' } = options;

  if (status === 'success') return null;

  if (status === 'timeout' || status === 'time_limit') {
    return buildGuidance(
      'timeout',
      'Превышено время выполнения',
      'Программа работала слишком долго и была остановлена.',
      [
        'Проверь, нет ли бесконечного цикла while True без break.',
        'Убедись, что цикл for имеет условие завершения.',
        'Возможно, программа выполняет слишком много повторений.',
      ],
      stderr || compileOutput,
    );
  }

  if (compileOutput.trim()) {
    return buildGuidance(
      'compile_error',
      'Ошибка компиляции',
      'Код не удалось скомпилировать перед запуском.',
      [
        'Проверь синтаксис: скобки, точки с запятой (в Java), объявление класса.',
        'Прочитай сообщение компилятора — там указана строка с ошибкой.',
        'Убедись, что все импорты и имена классов написаны правильно.',
      ],
      compileOutput,
    );
  }

  if (stderr.trim()) {
    return explainPythonStderr(stderr, sourceCode, stdin);
  }

  if (['wrong_answer', 'rejected', 'manual_review'].includes(status)) {
    return null;
  }

  return buildGuidance(
    'generic_runtime',
    'Ошибка выполнения',
    'Программа завершилась с ошибкой.',
    [
      'Попробуй запустить программу ещё раз.',
      'Проверь код на опечатки и логические ошибки.',
    ],
    '',
  );
}

export function resolveErrorGuidance(
  guidance: ErrorGuidance | undefined,
  options: {
    stderr?: string;
    compileOutput?: string;
    status?: string;
    sourceCode?: string;
    stdin?: string;
  },
): ErrorGuidance | undefined {
  if (guidance) return guidance;
  return parseExecutionError(options) ?? undefined;
}
