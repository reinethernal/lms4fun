import { useState } from 'react';
import { api } from '@/api/client';
import { CheckerFeedbackPanel } from '@/components/CheckerFeedbackPanel';
import { ErrorGuidance } from '@/components/ErrorGuidance';
import type { AdminSubmissionDetail } from '@/api/types';
import { statusBadgeClass, statusLabelRu } from '@/utils/submissionStatus';
import {
  extractCheckerFeedback,
  hasCheckerFeedback,
  shouldShowRuntimeErrors,
} from '@/utils/checkerFeedback';
import { isErrorGuidance } from '@/utils/errorGuidance';
import { resolveErrorGuidance } from '@/utils/parseExecutionError';

interface SubmissionDetailPanelProps {
  submission: AdminSubmissionDetail;
  onClose: () => void;
  mode?: 'staff' | 'readonly';
  onReview?: (updated: AdminSubmissionDetail) => void;
  onRecheck?: (id: number) => void;
}

export function SubmissionDetailPanel({
  submission,
  onClose,
  mode = 'readonly',
  onReview,
  onRecheck,
}: SubmissionDetailPanelProps) {
  const [comment, setComment] = useState(submission.teacher_comment || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const canReview =
    mode === 'staff' &&
    submission.status !== 'pending' &&
    submission.status !== 'running';

  async function handleReview(status: 'accepted' | 'rejected') {
    if (!onReview) return;
    setBusy(true);
    setError('');
    try {
      const updated = await api.admin.submissions.review(submission.id, {
        status,
        teacher_comment: comment,
      });
      onReview(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить проверку');
    } finally {
      setBusy(false);
    }
  }

  async function handleRecheck() {
    if (!onRecheck) return;
    setBusy(true);
    setError('');
    try {
      await api.admin.submissions.recheck(submission.id);
      onRecheck(submission.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить на перепроверку');
    } finally {
      setBusy(false);
    }
  }

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

  const checkerFeedback = extractCheckerFeedback(submission.checker_result);
  const showCheckerFeedback = hasCheckerFeedback(submission.status, checkerFeedback);
  const showRuntimeErrors = shouldShowRuntimeErrors({
    stderr: submission.stderr,
    status: submission.status,
    runtimeGuidance,
  });
  const showExecutionSection = Boolean(
    submission.stdout
    || submission.stderr
    || submission.compile_output
    || showRuntimeErrors
    || compileGuidance
    || showCheckerFeedback,
  );

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Решение #{submission.id}</h2>
        <p>
          <strong>{submission.user.display_name || submission.user.username}</strong>
          {' · '}
          {submission.task.title}
          {' · '}
          {submission.language}
        </p>
        <p>
          <span className={`badge ${statusBadgeClass(submission.status)}`}>
            {statusLabelRu(submission.status)}
          </span>
          {submission.score != null && <> · {submission.score}%</>}
          {submission.xp_awarded ? ` · +${submission.xp_awarded} XP` : ''}
          {submission.submitted_at && (
            <> · {new Date(submission.submitted_at).toLocaleString('ru-RU')}</>
          )}
        </p>
        {submission.checked_by && submission.checked_at && (
          <p className="hint-text">
            Проверил: {submission.checked_by.display_name || submission.checked_by.username}
            {' · '}
            {new Date(submission.checked_at).toLocaleString('ru-RU')}
          </p>
        )}
        {submission.teacher_comment && mode === 'readonly' && (
          <div className="card card-compact">
            <strong>Комментарий преподавателя:</strong>
            <p className="mt-sm">{submission.teacher_comment}</p>
          </div>
        )}
        {mode === 'staff' && (
          <div className="form-group">
            <label htmlFor="teacher-comment">Комментарий преподавателя</label>
            <textarea
              id="teacher-comment"
              className="input"
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Комментарий для ученика (необязательно)"
              disabled={busy}
            />
          </div>
        )}
        {error && <div className="error-banner">{error}</div>}
        <h3>Код</h3>
        <pre className="code-block">{submission.code || '—'}</pre>
        {showExecutionSection && (
          <>
            <h3>Результат выполнения</h3>
            {submission.stdout && (
              <>
                <p className="hint-text">Вывод программы</p>
                <pre className="code-block">{submission.stdout}</pre>
              </>
            )}
            {showCheckerFeedback && checkerFeedback && (
              <>
                <p className="hint-text">Результат проверки</p>
                <CheckerFeedbackPanel feedback={checkerFeedback} isStaff={mode === 'staff'} />
              </>
            )}
            {showRuntimeErrors && (
              <>
                <p className="hint-text">Ошибки выполнения</p>
                {runtimeGuidance ? (
                  <ErrorGuidance guidance={runtimeGuidance} variant="runtime" />
                ) : (
                  <pre className="code-block code-block-error">{submission.stderr}</pre>
                )}
              </>
            )}
            {(submission.compile_output || compileGuidance) && (
              <>
                <p className="hint-text">Ошибки компиляции</p>
                {compileGuidance ? (
                  <ErrorGuidance guidance={compileGuidance} variant="compile" />
                ) : (
                  <pre className="code-block">{submission.compile_output}</pre>
                )}
              </>
            )}
          </>
        )}
        <div className="modal-actions">
          {mode === 'staff' && (
            <>
              {canReview && (
                <>
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={() => void handleReview('accepted')}
                  >
                    Принять
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    disabled={busy}
                    onClick={() => void handleReview('rejected')}
                  >
                    Отклонить
                  </button>
                </>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                disabled={busy || submission.status === 'pending' || submission.status === 'running'}
                onClick={() => void handleRecheck()}
              >
                Перепроверить
              </button>
            </>
          )}
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
