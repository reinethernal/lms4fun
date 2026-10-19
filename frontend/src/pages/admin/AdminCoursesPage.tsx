import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import type { Course, ProgrammingLanguage } from '@/api/types';
import { Loading } from '@/components/Loading';

export function AdminCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [languages, setLanguages] = useState<ProgrammingLanguage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Course | null>(null);
  const [form, setForm] = useState({
    title: '',
    slug: '',
    description: '',
    primary_language_id: '',
    level: 'beginner',
    status: 'draft',
    visibility: 'private',
  });

  async function load() {
    try {
      const [coursesData, langs] = await Promise.all([
        api.admin.courses.list(),
        api.languages.list(),
      ]);
      setCourses(coursesData);
      setLanguages(langs);
    } catch {
      setError('Не удалось загрузить курсы');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openCreate() {
    setEditing(null);
    setForm({
      title: '',
      slug: '',
      description: '',
      primary_language_id: languages[0] ? String(languages[0].id) : '',
      level: 'beginner',
      status: 'draft',
      visibility: 'private',
    });
    setShowModal(true);
  }

  function openEdit(course: Course) {
    setEditing(course);
    setForm({
      title: course.title,
      slug: course.slug,
      description: course.description,
      primary_language_id: course.primary_language ? String(course.primary_language.id) : '',
      level: course.level,
      status: course.status,
      visibility: course.visibility,
    });
    setShowModal(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    const payload = {
      title: form.title,
      slug: form.slug,
      description: form.description,
      primary_language_id: Number(form.primary_language_id),
      level: form.level,
      status: form.status,
      visibility: form.visibility,
    };
    try {
      if (editing) {
        await api.admin.courses.update(editing.id, payload);
      } else {
        await api.admin.courses.create(payload);
      }
      setShowModal(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  async function handleDelete(course: Course) {
    if (!confirm(`Удалить курс «${course.title}»?`)) return;
    try {
      await api.admin.courses.delete(course.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">Курсы</h1>
      {error && <div className="error-banner">{error}</div>}

      <div className="admin-actions">
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Добавить
        </button>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th className="col-hide-mobile">ID</th>
                <th>Название</th>
                <th>Язык</th>
                <th>Уровень</th>
                <th>Статус</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {courses.map((course) => (
                <tr key={course.id}>
                  <td className="col-hide-mobile">{course.id}</td>
                  <td>{course.title}</td>
                  <td>{course.primary_language?.name ?? '—'}</td>
                  <td>{course.level}</td>
                  <td>
                    <span className={`badge ${course.status === 'published' ? 'badge-success' : 'badge-warning'}`}>
                      {course.status}
                    </span>
                  </td>
                  <td>
                    <Link
                      to={`/admin/courses/${course.id}/lessons`}
                      className="btn btn-secondary btn-compact mr-sm"
                    >
                      Уроки
                    </Link>
                    <button type="button" className="btn btn-secondary btn-compact mr-sm" onClick={() => openEdit(course)}>
                      Изменить
                    </button>
                    <button type="button" className="btn btn-danger btn-compact" onClick={() => void handleDelete(course)}>
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editing ? 'Редактировать курс' : 'Новый курс'}</h2>
            <form onSubmit={(e) => void handleSubmit(e)}>
              <div className="form-group">
                <label>Название</label>
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Slug</label>
                <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
              </div>
              <div className="form-group">
                <label>Основной язык</label>
                <select value={form.primary_language_id} onChange={(e) => setForm({ ...form, primary_language_id: e.target.value })} required>
                  {languages.map((l) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Уровень</label>
                <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
                  <option value="beginner">Начальный</option>
                  <option value="intermediate">Средний</option>
                  <option value="advanced">Продвинутый</option>
                </select>
              </div>
              <div className="form-group">
                <label>Статус</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="draft">Черновик</option>
                  <option value="published">Опубликован</option>
                  <option value="archived">Архив</option>
                </select>
              </div>
              <div className="form-group">
                <label>Видимость</label>
                <select value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })}>
                  <option value="private">Приватный</option>
                  <option value="public">Публичный</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
                <button type="submit" className="btn btn-primary">Сохранить</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
