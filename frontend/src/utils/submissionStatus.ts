export function statusBadgeClass(status: string): string {
  if (status === 'accepted' || status === 'success') return 'badge-success';
  if (status === 'pending' || status === 'running') return 'badge-warning';
  if (status === 'manual_review') return 'badge-info';
  return 'badge-danger';
}

export function statusLabelRu(status: string): string {
  const map: Record<string, string> = {
    success: 'Выполнено',
    accepted: 'Зачтено',
    pending: 'Проверяется…',
    running: 'Проверяется…',
    manual_review: 'На проверке',
    wrong_answer: 'Нужно исправить',
    compile_error: 'Ошибка компиляции',
    runtime_error: 'Ошибка выполнения',
    time_limit: 'Превышено время',
    rejected: 'Нужно исправить',
    error: 'Нужно исправить',
    waiting_input: 'Ждёт ввод',
  };
  return map[status] ?? status;
}

export function countInputCalls(code: string): number {
  return (code.match(/\binput\s*\(/g) ?? []).length;
}

export function taskNeedsStdin(
  code: string,
  task: { requires_stdin?: boolean; visible_tests_json?: unknown } | null,
): boolean {
  if (task?.requires_stdin) return true;
  if (/\binput\s*\(/.test(code)) return true;
  if (!task?.visible_tests_json) return false;
  const tests = task.visible_tests_json;
  if (!Array.isArray(tests)) return false;
  return tests.some(
    (t) => typeof t === 'object' && t !== null && 'stdin' in t && Boolean((t as { stdin?: string }).stdin),
  );
}

import type { ErrorGuidance } from './errorGuidance';
import { isErrorGuidance } from './errorGuidance';

export function formatGuidanceForBanner(guidance: ErrorGuidance | undefined): string {
  if (!guidance) return '';
  const parts = [guidance.summary];
  if (guidance.attention.length > 0) {
    parts.push(`Обрати внимание: ${guidance.attention[0]}`);
  }
  return parts.filter(Boolean).join('\n');
}

export function pollDataFromSubmission(detail: {
  id: number;
  status: string;
  xp_awarded: number;
  stdout?: string;
  stderr?: string;
  compile_output?: string;
  checker_result?: Record<string, unknown> | null;
}) {
  const checker = detail.checker_result ?? {};
  const errorGuidance = isErrorGuidance(checker.error_guidance)
    ? checker.error_guidance
    : undefined;
  return {
    status: detail.status,
    xp_awarded: detail.xp_awarded,
    message: typeof checker.message === 'string' ? checker.message : '',
    new_badges: Array.isArray(checker.new_badges) ? checker.new_badges : [],
    failed_test_index: checker.failed_test_index,
    expected: typeof checker.expected === 'string' ? checker.expected : undefined,
    got: typeof checker.got === 'string' ? checker.got : undefined,
    is_hidden: typeof checker.is_hidden === 'boolean' ? checker.is_hidden : undefined,
    error_guidance: errorGuidance,
    stdout: detail.stdout,
    stderr: detail.stderr,
    compile_output: detail.compile_output,
  };
}
