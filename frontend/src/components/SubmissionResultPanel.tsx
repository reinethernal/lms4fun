import type { AdminSubmissionDetail } from '@/api/types';
import { CheckerFeedbackPanel } from '@/components/CheckerFeedbackPanel';
import { ErrorGuidance } from '@/components/ErrorGuidance';
import {
  extractCheckerFeedback,
  hasCheckerFeedback,
  shouldShowRuntimeErrors,
} from '@/utils/checkerFeedback';
import { isErrorGuidance } from '@/utils/errorGuidance';
import { resolveErrorGuidance } from '@/utils/parseExecutionError';

interface SubmissionResultPanelProps {
  submission: AdminSubmissionDetail;
}

export function SubmissionResultPanel({ submission }: SubmissionResultPanelProps) {
  const { status } = submission;

  if (status === 'pending' || status === 'running') {
    return null;
  }

  if (status === 'accepted') {
    return (
      <div className="submission-result mt-md">
        <div className="success-banner">
          Задание зачтено!
          {submission.xp_awarded ? ` +${submission.xp_awarded} XP` : ''}
        </div>
      </div>
    );
  }

  if (status === 'manual_review') {
    return (
      <div className="submission-result mt-md">
        <div className="info-banner">
          Решение отправлено на проверку преподавателю. Статус урока: «На проверке».
        </div>
      </div>
    );
  }

  const checkerFeedback = extractCheckerFeedback(submission.checker_result);
  const showCheckerFeedback = hasCheckerFeedback(status, checkerFeedback);
  const checkerGuidance = isErrorGuidance(submission.checker_result?.error_guidance)
    ? submission.checker_result.error_guidance
    : undefined;
  const runtimeGuidance = resolveErrorGuidance(checkerGuidance, {
    stderr: submission.stderr,
    compileOutput: submission.compile_output,
    status: submission.status,
    sourceCode: submission.code,
  });
  const compileGuidance = submission.compile_output
    ? resolveErrorGuidance(undefined, {
        compileOutput: submission.compile_output,
        status: 'compile_error',
        sourceCode: submission.code,
      })
    : undefined;
  const showRuntimeErrors = shouldShowRuntimeErrors({
    stderr: submission.stderr,
    status: submission.status,
    runtimeGuidance,
  });

  return (
    <div className="submission-result mt-md card card-compact">
      <h3 className="submission-result-title">Результат проверки</h3>

      {showCheckerFeedback && checkerFeedback && (
        <>
          <p className="hint-text">Сравнение с эталоном</p>
          <CheckerFeedbackPanel feedback={checkerFeedback} isStaff={false} />
        </>
      )}

      {showRuntimeErrors && (
        <>
          <p className="hint-text">Ошибка выполнения</p>
          {runtimeGuidance ? (
            <ErrorGuidance guidance={runtimeGuidance} variant="runtime" />
          ) : (
            <pre className="code-block code-block-error">{submission.stderr}</pre>
          )}
        </>
      )}

      {(submission.compile_output || compileGuidance) && (
        <>
          <p className="hint-text">Ошибка компиляции</p>
          {compileGuidance ? (
            <ErrorGuidance guidance={compileGuidance} variant="compile" />
          ) : (
            <pre className="code-block">{submission.compile_output}</pre>
          )}
        </>
      )}

      {!showCheckerFeedback && !showRuntimeErrors && !submission.compile_output && !compileGuidance && (
        <p className="hint-text">Решение нужно исправить. Попробуй ещё раз.</p>
      )}
    </div>
  );
}

function submitBannerClass(status: string): string {
  if (status === 'accepted') return 'success-banner';
  if (status === 'manual_review' || status === 'pending' || status === 'running') {
    return 'info-banner';
  }
  return 'error-banner';
}

export function submissionBannerClass(status: string): string {
  return submitBannerClass(status);
}

export function submissionBannerMessage(submission: AdminSubmissionDetail): string {
  const checker = submission.checker_result ?? {};
  const message = typeof checker.message === 'string' ? checker.message : '';

  if (submission.status === 'accepted') {
    return submission.xp_awarded
      ? `Задание зачтено! +${submission.xp_awarded} XP`
      : 'Задание зачтено!';
  }
  if (submission.status === 'manual_review') {
    return 'Решение на проверке у преподавателя.';
  }
  if (submission.status === 'wrong_answer') {
    return 'Ответ не совпал с эталоном — см. подробности ниже.';
  }
  if (submission.status === 'runtime_error' || submission.status === 'compile_error') {
    return 'В программе ошибка — см. подробности ниже.';
  }
  return message || 'Решение нужно исправить.';
}
