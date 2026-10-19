import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import type { AdminTask, Lesson, ProgrammingLanguage } from '@/api/types';
import { LessonImportModal } from '@/components/LessonImportModal';
import { Loading } from '@/components/Loading';

export function AdminLessonEditPage() {
  const { lessonId } = useParams<{ lessonId: string }>();
  const lessonIdNum = Number(lessonId);
  const navigate = useNavigate();

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [tasks, setTasks] = useState<AdminTask[]>([]);
  const [languages, setLanguages] = useState<ProgrammingLanguage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showImportTasks, setShowImportTasks] = useState(false);
  const [form, setForm] = useState({
    number: '1',
    title: '',
    slug: '',
    language: '',
    status: 'draft',
    goal: '',
    theory_text: '',
    simple_explanation: '',
    practice_text: '',
    mini_project_text: '',
    summary_text: '',
    max_xp: '0',
    sort_order: '0',
    version: '1.0',
    content_format: 'markdown',
  });

  async function load() {
    if (!lessonIdNum) return;
    try {
      const [lessonData, tasksData, langs] = await Promise.all([
        api.admin.lessons.get(lessonIdNum),
        api.admin.tasks.list(lessonIdNum),
        api.languages.list(),
      ]);
      setLesson(lessonData);
      setTasks(tasksData.sort((a, b) => a.sort_order - b.sort_order));
      setLanguages(langs);
      setForm({
        number: String(lessonData.number),
        title: lessonData.title,
        slug: lessonData.slug,
        language: lessonData.language ? String(lessonData.language) : '',
        status: lessonData.status,
        goal: lessonData.goal || '',
        theory_text: lessonData.theory_text || '',
        simple_explanation: lessonData.simple_explanation || '',
        practice_text: lessonData.practice_text || '',
        mini_project_text: lessonData.mini_project_text || '',
        summary_text: lessonData.summary_text || '',
        max_xp: String(lessonData.max_xp ?? 0),
        sort_order: String(lessonData.sort_order ?? 0),
        version: lessonData.version || '1.0',
        content_format: lessonData.content_format || 'markdown',
      });
    } catch {
      setError('Не удалось загрузить урок');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [lessonIdNum]);

  async function handleSaveLesson(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.admin.lessons.update(lessonIdNum, {
        number: Number(form.number),
        title: form.title,
        slug: form.slug,
        language: Number(form.language),
        status: form.status,
        goal: form.goal,
        theory_text: form.theory_text,
        simple_explanation: form.simple_explanation,
        practice_text: form.practice_text,
        mini_project_text: form.mini_project_text,
        summary_text: form.summary_text,
        max_xp: Number(form.max_xp),
        sort_order: Number(form.sort_order),
        version: form.version,
        content_format: form.content_format,
      });
      setSuccess('Урок сохранён');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  async function handleDeleteTask(task: AdminTask) {
    if (!confirm(`Удалить задание «${task.title}»?`)) return;
    try {
      await api.admin.tasks.delete(task.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  if (loading) return <Loading />;
  if (!lesson) return <div className="error-banner">Урок не найден</div>;

  return (
    <div>
      <p>
        <Link to={`/admin/courses/${lesson.course}/lessons`}>← Уроки курса</Link>
      </p>
      <h1 className="page-title">Редактирование: {lesson.title}</h1>
      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <form onSubmit={(e) => void handleSaveLesson(e)} className="card mt-md">
        <h2>Метаданные</h2>
        <div className="form-row-grid">
          <div className="form-group">
            <label>Номер</label>
            <input
              type="number"
              value={form.number}
              onChange={(e) => setForm({ ...form, number: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Slug</label>
            <input
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Язык</label>
            <select
              value={form.language}
              onChange={(e) => setForm({ ...form, language: e.target.value })}
              required
            >
              {languages.map((l) => (
                <option key={l.id} value={l.id}>{l.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Статус</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              <option value="draft">Черновик</option>
              <option value="published">Опубликован</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div className="form-group">
            <label>Max XP</label>
            <input
              type="number"
              value={form.max_xp}
              onChange={(e) => setForm({ ...form, max_xp: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Порядок</label>
            <input
              type="number"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
            />
          </div>
        </div>
        <div className="form-group">
          <label>Название</label>
          <input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
        </div>
        <div className="form-group">
          <label>Цель</label>
          <textarea
            value={form.goal}
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
            rows={2}
          />
        </div>

        <h2 className="mt-lg">Контент</h2>
        <div className="form-group">
          <label>Теория</label>
          <textarea
            value={form.theory_text}
            onChange={(e) => setForm({ ...form, theory_text: e.target.value })}
            rows={8}
          />
        </div>
        <div className="form-group">
          <label>Простыми словами</label>
          <textarea
            value={form.simple_explanation}
            onChange={(e) => setForm({ ...form, simple_explanation: e.target.value })}
            rows={4}
          />
        </div>
        <div className="form-group">
          <label>Практика</label>
          <textarea
            value={form.practice_text}
            onChange={(e) => setForm({ ...form, practice_text: e.target.value })}
            rows={4}
          />
        </div>
        <div className="form-group">
          <label>Мини-проект</label>
          <textarea
            value={form.mini_project_text}
            onChange={(e) => setForm({ ...form, mini_project_text: e.target.value })}
            rows={4}
          />
        </div>
        <div className="form-group">
          <label>Итог</label>
          <textarea
            value={form.summary_text}
            onChange={(e) => setForm({ ...form, summary_text: e.target.value })}
            rows={3}
          />
        </div>
        <button type="submit" className="btn btn-primary">Сохранить урок</button>
      </form>

      <div className="mt-xl">
        <div className="page-header-row">
          <h2>Задания</h2>
          <div className="flex-wrap-gap">
            <button
              type="button"
              className="btn btn-primary btn-compact"
              onClick={() => navigate(`/admin/lessons/${lessonIdNum}/tasks/new`)}
            >
              + Добавить задание
            </button>
            <button type="button" className="btn btn-secondary btn-compact" onClick={() => setShowImportTasks(true)}>
              Импорт заданий
            </button>
          </div>
        </div>
        <div className="card mt-md">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th className="col-hide-mobile">Тип</th>
                  <th className="col-hide-mobile">Проверка</th>
                  <th>XP</th>
                  <th className="col-hide-mobile">Обяз.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tasks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center-muted">Заданий пока нет</td>
                  </tr>
                ) : (
                  tasks.map((task) => (
                    <tr key={task.id}>
                      <td>{task.title}</td>
                      <td className="col-hide-mobile">{task.task_type}</td>
                      <td className="col-hide-mobile">{task.checker_type}</td>
                      <td>{task.max_xp}</td>
                      <td className="col-hide-mobile">{task.is_required ? 'Да' : 'Нет'}</td>
                      <td>
                        <Link
                          to={`/admin/lessons/${lessonIdNum}/tasks/${task.id}/edit`}
                          className="btn btn-secondary btn-compact mr-sm"
                        >
                          Изменить
                        </Link>
                        <button
                          type="button"
                          className="btn btn-danger btn-compact"
                          onClick={() => void handleDeleteTask(task)}
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showImportTasks && lesson && (
        <LessonImportModal
          mode="tasks"
          courseId={lesson.course}
          lessonId={lessonIdNum}
          onClose={() => setShowImportTasks(false)}
          onSuccess={() => void load()}
        />
      )}
    </div>
  );
}
