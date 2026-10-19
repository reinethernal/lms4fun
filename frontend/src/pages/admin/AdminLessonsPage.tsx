import { FormEvent, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import type { Course, Lesson, ProgrammingLanguage } from '@/api/types';
import { LessonImportModal } from '@/components/LessonImportModal';
import { Loading } from '@/components/Loading';

type ImportMode = 'lesson' | 'course' | 'tasks' | null;

export function AdminLessonsPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const courseIdNum = Number(courseId);

  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [languages, setLanguages] = useState<ProgrammingLanguage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [importMode, setImportMode] = useState<ImportMode>(null);
  const [importLessonId, setImportLessonId] = useState<number | null>(null);
  const [form, setForm] = useState({
    number: '1',
    title: '',
    slug: '',
    language: '',
    status: 'draft',
    goal: '',
  });

  async function load() {
    if (!courseIdNum) return;
    try {
      const [courseData, lessonsData, langs] = await Promise.all([
        api.admin.courses.get(courseIdNum),
        api.admin.lessons.list(courseIdNum),
        api.languages.list(),
      ]);
      setCourse(courseData);
      setLessons(
        lessonsData.sort((a, b) => a.sort_order - b.sort_order || a.number - b.number),
      );
      setLanguages(langs);
    } catch {
      setError('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [courseIdNum]);

  function openCreate() {
    const defaultLang = course?.primary_language?.id ?? languages[0]?.id;
    const nextNumber = lessons.length > 0
      ? String(Math.max(...lessons.map((l) => l.number)) + 1)
      : '1';
    setForm({
      number: nextNumber,
      title: '',
      slug: '',
      language: defaultLang ? String(defaultLang) : '',
      status: 'draft',
      goal: '',
    });
    setShowCreate(true);
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await api.admin.lessons.create({
        course: courseIdNum,
        number: Number(form.number),
        title: form.title,
        slug: form.slug,
        language: Number(form.language),
        status: form.status,
        goal: form.goal,
        theory_text: '',
        practice_text: '',
        sort_order: Number(form.number),
      });
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания');
    }
  }

  async function handleDelete(lesson: Lesson) {
    if (!confirm(`Удалить урок «${lesson.title}»?`)) return;
    try {
      await api.admin.lessons.delete(lesson.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  async function handleExport() {
    try {
      await api.admin.export.course(courseIdNum);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка экспорта');
    }
  }

  function langName(langId?: number) {
    return languages.find((l) => l.id === langId)?.name ?? '—';
  }

  if (loading) return <Loading />;
  if (!course) return <div className="error-banner">Курс не найден</div>;

  return (
    <div>
      <p>
        <Link to="/admin/courses">← Курсы</Link>
      </p>
      <h1 className="page-title">Уроки: {course.title}</h1>
      {error && <div className="error-banner">{error}</div>}

      <div className="admin-actions flex-wrap-gap">
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Добавить урок
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setImportMode('lesson')}>
          Загрузить урок
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setImportMode('course')}>
          Импорт курса
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => void handleExport()}>
          Экспорт курса
        </button>
      </div>

      <div className="card mt-md">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>№</th>
                <th>Название</th>
                <th className="col-hide-mobile">Язык</th>
                <th>Статус</th>
                <th className="col-hide-mobile">XP</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lessons.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center-muted">
                    Уроков пока нет
                  </td>
                </tr>
              ) : (
                lessons.map((lesson) => (
                  <tr key={lesson.id}>
                    <td>{lesson.number}</td>
                    <td>{lesson.title}</td>
                    <td className="col-hide-mobile">{langName(lesson.language)}</td>
                    <td>
                      <span className={`badge ${lesson.status === 'published' ? 'badge-success' : 'badge-warning'}`}>
                        {lesson.status}
                      </span>
                    </td>
                    <td className="col-hide-mobile">{lesson.max_xp}</td>
                    <td>
                      <Link
                        to={`/admin/lessons/${lesson.id}/edit`}
                        className="btn btn-secondary btn-compact mr-sm"
                      >
                        Редактировать
                      </Link>
                      <button
                        type="button"
                        className="btn btn-secondary btn-compact mr-sm"
                        onClick={() => {
                          setImportLessonId(lesson.id);
                          setImportMode('tasks');
                        }}
                      >
                        Импорт заданий
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-compact"
                        onClick={() => void handleDelete(lesson)}
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

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Новый урок</h2>
            <form onSubmit={(e) => void handleCreate(e)}>
              <div className="form-group">
                <label>Номер</label>
                <input
                  type="number"
                  value={form.number}
                  onChange={(e) => setForm({ ...form, number: e.target.value })}
                  required
                  min={1}
                />
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
                <label>Цель</label>
                <textarea
                  value={form.goal}
                  onChange={(e) => setForm({ ...form, goal: e.target.value })}
                  rows={2}
                />
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
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn btn-primary">Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {importMode && (
        <LessonImportModal
          mode={importMode}
          courseId={courseIdNum}
          lessonId={importLessonId ?? undefined}
          onClose={() => {
            setImportMode(null);
            setImportLessonId(null);
          }}
          onSuccess={() => void load()}
        />
      )}
    </div>
  );
}
