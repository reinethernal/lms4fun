import type { CheckerFeedback } from '@/utils/checkerFeedback';
import {
  HIDDEN_TEST_STUDENT_MESSAGE,
  visibleExpectedGot,
} from '@/utils/checkerFeedback';

interface CheckerFeedbackPanelProps {
  feedback: CheckerFeedback;
  isStaff: boolean;
}

export function CheckerFeedbackPanel({ feedback, isStaff }: CheckerFeedbackPanelProps) {
  const showComparison = visibleExpectedGot(feedback, isStaff);

  if (!showComparison && feedback.isHidden && !isStaff) {
    return (
      <div className="checker-feedback">
        <p className="hint-text">{HIDDEN_TEST_STUDENT_MESSAGE}</p>
      </div>
    );
  }

  if (showComparison && (feedback.expected !== undefined || feedback.got !== undefined)) {
    return (
      <div className="checker-feedback">
        {feedback.expected !== undefined && (
          <div className="checker-feedback-row">
            <p className="checker-feedback-label">Ожидалось</p>
            <pre className="code-block">{feedback.expected || '—'}</pre>
          </div>
        )}
        {feedback.got !== undefined && (
          <div className="checker-feedback-row">
            <p className="checker-feedback-label">Получено</p>
            <pre className="code-block code-block-error">{feedback.got || '—'}</pre>
          </div>
        )}
      </div>
    );
  }

  if (feedback.message) {
    return (
      <div className="checker-feedback">
        <pre className="code-block">{feedback.message}</pre>
      </div>
    );
  }

  return null;
}
