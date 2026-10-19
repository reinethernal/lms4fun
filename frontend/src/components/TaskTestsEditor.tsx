import type { TaskTestCase } from '@/api/types';

interface TaskTestsEditorProps {
  label: string;
  tests: TaskTestCase[];
  onChange: (tests: TaskTestCase[]) => void;
  showHidden?: boolean;
}

const emptyTest = (): TaskTestCase => ({
  stdin: '',
  expected_stdout: '',
});

export function TaskTestsEditor({ label, tests, onChange, showHidden }: TaskTestsEditorProps) {
  function updateRow(index: number, patch: Partial<TaskTestCase>) {
    onChange(tests.map((t, i) => (i === index ? { ...t, ...patch } : t)));
  }

  function addRow() {
    onChange([...tests, showHidden ? { ...emptyTest(), hidden: true } : emptyTest()]);
  }

  function removeRow(index: number) {
    onChange(tests.filter((_, i) => i !== index));
  }

  return (
    <div className="form-group">
      <div className="page-header-row">
        <label>{label}</label>
        <button type="button" className="btn btn-secondary btn-compact" onClick={addRow}>
          + Тест
        </button>
      </div>
      {tests.length === 0 ? (
        <p className="hint-text">Тестов пока нет</p>
      ) : (
        tests.map((test, index) => (
          <div key={index} className={`card card-compact${index > 0 ? ' mt-md' : ''}`}>
              <div className="page-header-row mb-sm">
                <strong>Тест #{index + 1}</strong>
                <button
                  type="button"
                  className="btn btn-danger btn-compact"
                  onClick={() => removeRow(index)}
                >
                  Удалить
                </button>
              </div>
              <div className="form-group">
                <label>stdin</label>
                <textarea
                  className="code-textarea"
                  rows={2}
                  value={test.stdin ?? ''}
                  onChange={(e) => updateRow(index, { stdin: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>expected_stdout</label>
                <textarea
                  className="code-textarea"
                  rows={2}
                  value={test.expected_stdout ?? ''}
                  onChange={(e) => updateRow(index, { expected_stdout: e.target.value })}
                />
              </div>
              {showHidden && (
                <label>
                  <input
                    type="checkbox"
                    checked={Boolean(test.hidden)}
                    onChange={(e) => updateRow(index, { hidden: e.target.checked })}
                  />
                  {' '}Скрытый тест
                </label>
              )}
            </div>
          ))
      )}
    </div>
  );
}
