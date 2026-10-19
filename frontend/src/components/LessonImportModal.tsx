import { FormEvent, useState } from 'react';
import { api } from '@/api/client';
import type { ImportJob } from '@/api/types';

type ImportMode = 'lesson' | 'course' | 'tasks';

interface LessonImportModalProps {
  mode: ImportMode;
  courseId: number;
  lessonId?: number;
  onClose: () => void;
  onSuccess: () => void;
}

const modeLabels: Record<ImportMode, string> = {
  course: 'Импорт курса (JSON/ZIP)',
  lesson: 'Импорт урока (JSON/MD)',
  tasks: 'Импорт заданий (JSON)',
};

const modeAccept: Record<ImportMode, string> = {
  course: '.json,.zip',
  lesson: '.json,.md',
  tasks: '.json',
};

export function LessonImportModal({
  mode,
  courseId,
  lessonId,
  onClose,
  onSuccess,
}: LessonImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ImportJob | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setError('Выберите файл');
      return;
    }
    setSubmitting(true);
    setError('');
    setResult(null);
    try {
      let job: ImportJob;
      if (mode === 'course') {
        job = await api.admin.import.course(file);
      } else if (mode === 'lesson') {
        job = await api.admin.import.lesson(file, courseId);
      } else {
        if (!lessonId) {
          setError('Не выбран урок');
          return;
        }
        job = await api.admin.import.tasks(file, lessonId);
      }
      setResult(job);
      if (job.status === 'completed') {
        onSuccess();
      } else if (job.status === 'failed') {
        setError(job.errors_json?.join('; ') || 'Импорт не удался');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка импорта');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{modeLabels[mode]}</h2>
        {error && <div className="error-banner">{error}</div>}
        {result && result.status !== 'failed' && (
          <div className="success-banner">Импорт выполнен: {result.file_name}</div>
        )}
        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="form-group">
            <label>Файл</label>
            <input
              type="file"
              accept={modeAccept[mode]}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              required
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              {result && result.status !== 'failed' ? 'Закрыть' : 'Отмена'}
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Загрузка…' : 'Импортировать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
