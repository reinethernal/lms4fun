const CHECKER_FEEDBACK_STATUSES = new Set(['wrong_answer', 'rejected', 'manual_review']);

export interface CheckerFeedback {
  message: string;
  expected?: string;
  got?: string;
  isHidden: boolean;
  failedTestIndex?: number;
}

export function extractCheckerFeedback(
  checkerResult: Record<string, unknown> | null | undefined,
): CheckerFeedback | null {
  if (!checkerResult) return null;

  const message = typeof checkerResult.message === 'string' ? checkerResult.message : '';
  const expected = typeof checkerResult.expected === 'string' ? checkerResult.expected : undefined;
  const got = typeof checkerResult.got === 'string' ? checkerResult.got : undefined;
  const isHidden = checkerResult.is_hidden === true;
  const failedTestIndex = typeof checkerResult.failed_test_index === 'number'
    ? checkerResult.failed_test_index
    : undefined;

  if (!message && expected === undefined && got === undefined) {
    return null;
  }

  return { message, expected, got, isHidden, failedTestIndex };
}

export function hasCheckerFeedback(status: string, feedback: CheckerFeedback | null): boolean {
  if (status === 'accepted' || status === 'pending' || status === 'running') {
    return false;
  }
  if (!feedback || !CHECKER_FEEDBACK_STATUSES.has(status)) {
    return false;
  }
  return Boolean(feedback.message || feedback.expected !== undefined || feedback.got !== undefined);
}

export function visibleExpectedGot(feedback: CheckerFeedback, isStaff: boolean): boolean {
  if (feedback.expected === undefined && feedback.got === undefined) {
    return false;
  }
  return isStaff || !feedback.isHidden;
}

export const HIDDEN_TEST_STUDENT_MESSAGE =
  'Ответ не совпал с эталоном. Попробуй ещё раз.';

export function shouldShowRuntimeErrors(options: {
  stderr?: string;
  status: string;
  runtimeGuidance?: { raw?: string };
}): boolean {
  const { stderr = '', status, runtimeGuidance } = options;
  if (stderr.trim()) return true;
  if (['runtime_error', 'time_limit', 'error'].includes(status)) return true;
  if (runtimeGuidance?.raw?.trim()) return true;
  return false;
}
