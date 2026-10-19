import type { ErrorGuidance } from '@/utils/errorGuidance';

interface ErrorGuidanceProps {
  guidance: ErrorGuidance;
  variant?: 'runtime' | 'compile';
  onFocusInput?: () => void;
}

export function ErrorGuidance({ guidance, variant = 'runtime', onFocusInput }: ErrorGuidanceProps) {
  const raw = guidance.raw?.trim();

  return (
    <div className={`error-guidance error-guidance-${variant}`}>
      <p className="error-guidance-title">{guidance.title}</p>
      <p className="error-guidance-summary">
        <strong>Что случилось:</strong> {guidance.summary}
      </p>
      {guidance.why && (
        <p className="error-guidance-why">
          <strong>Почему так происходит:</strong> {guidance.why}
        </p>
      )}
      {guidance.attention.length > 0 && (
        <div className="error-guidance-attention">
          <p className="error-guidance-attention-label">Обрати внимание:</p>
          <ul>
            {guidance.attention.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </div>
      )}
      {guidance.error_type === 'eof_error' && onFocusInput && (
        <button type="button" className="btn btn-secondary btn-sm error-guidance-action" onClick={onFocusInput}>
          Перейти к полю ввода
        </button>
      )}
      {guidance.line != null && (
        <p className="error-guidance-line hint-text">Строка в коде: {guidance.line}</p>
      )}
      {raw && (
        <details className="error-guidance-details">
          <summary>Технические детали</summary>
          <pre className="error-guidance-raw">{raw}</pre>
        </details>
      )}
    </div>
  );
}
