import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { Badge, Course } from '@/api/types';
import { Loading } from '@/components/Loading';

const BADGE_TYPES = [
  { value: 'achievement', label: 'Достижение' },
  { value: 'course', label: 'Курс' },
  { value: 'language', label: 'Язык' },
  { value: 'special', label: 'Особый' },
  { value: 'project', label: 'Проект' },
  { value: 'style', label: 'Стиль' },
  { value: 'debug', label: 'Отладка' },
  { value: 'soft_skill', label: 'Навык' },
  { value: 'social', label: 'Социальный' },
  { value: 'final_project', label: 'Финальный проект' },
];

const BADGE_LEVELS = [
  { value: 'bronze', label: 'Бронза' },
  { value: 'silver', label: 'Серебро' },
  { value: 'gold', label: 'Золото' },
  { value: 'platinum', label: 'Платина' },
  { value: 'legendary', label: 'Легенда' },
];

const CONDITION_TYPES = [
  { value: '', label: '—' },
  { value: 'xp_total', label: 'Всего XP' },
  { value: 'tasks_completed', label: 'Заданий выполнено' },
  { value: 'lessons_completed', label: 'Уроков пройдено' },
  { value: 'course_completed', label: 'Курс завершён' },
  { value: 'manual', label: 'Вручную' },
];

const emptyForm = {
  title: '',
  description: '',
  icon: '',
  badge_type: 'achievement',
  level: 'bronze',
  condition_type: '',
  condition_key: '',
  condition_value: '',
  condition_params: '{}',
  course_id: '',
  is_active: true,
};

function levelLabel(level: string): string {
  return BADGE_LEVELS.find((l) => l.value === level)?.label ?? level;
}

function conditionLabel(badge: Badge): string {
  const key = badge.condition_key || badge.condition_type;
  if (!key) return '—';
  const params = badge.condition_params && Object.keys(badge.condition_params).length > 0
    ? ` ${JSON.stringify(badge.condition_params)}`
    : '';
  const value = badge.condition_value != null ? ` (${badge.condition_value})` : '';
  return `${key}${value}${params}`;
}

function BadgeIconPreview({ badge }: { badge: Badge }) {
  const isLegendary = badge.level === 'legendary';
  const content = badge.icon_url && badge.icon_url.startsWith('http') ? (
    <img
      src={badge.icon_url}
      alt=""
      className="badge-icon-sm"
    />
  ) : (
    <span className="icon-fallback">{badge.icon_url || '—'}</span>
  );

  return (
    <span className={`badge-icon-preview badge-level-${badge.level || 'bronze'}`}>
      {isLegendary && <span className="badge-crown" aria-hidden>👑</span>}
      {content}
    </span>
  );
}

export function AdminBadgesPage() {
  const [badges, setBadges] = useState<Badge[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Badge | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [iconFile, setIconFile] = useState<File | null>(null);

  async function load() {
    try {
      const [badgesData, coursesData] = await Promise.all([
        api.admin.badges.list(),
        api.admin.courses.list(),
      ]);
      setBadges(badgesData);
      setCourses(coursesData);
    } catch {
      setError('Не удалось загрузить бейджи');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setIconFile(null);
    setShowModal(true);
  }

  function openEdit(badge: Badge) {
    setEditing(badge);
    setForm({
      title: badge.title,
      description: badge.description,
      icon: badge.icon,
      badge_type: badge.badge_type,
      level: badge.level || 'bronze',
      condition_type: badge.condition_type || '',
      condition_key: badge.condition_key || '',
      condition_value: badge.condition_value != null ? String(badge.condition_value) : '',
      condition_params: JSON.stringify(badge.condition_params || {}, null, 2),
      course_id: badge.course != null ? String(badge.course) : '',
      is_active: badge.is_active,
    });
    setIconFile(null);
    setShowModal(true);
  }

  function buildFormData(): FormData {
    const data = new FormData();
    data.append('title', form.title);
    data.append('description', form.description);
    data.append('icon', form.icon);
    data.append('badge_type', form.badge_type);
    data.append('level', form.level);
    data.append('condition_type', form.condition_type);
    data.append('condition_key', form.condition_key);
    if (form.condition_value) {
      data.append('condition_value', form.condition_value);
    }
    try {
      const params = form.condition_params.trim() ? JSON.parse(form.condition_params) : {};
      data.append('condition_params', JSON.stringify(params));
    } catch {
      data.append('condition_params', '{}');
    }
    if (form.course_id) {
      data.append('course', form.course_id);
    }
    data.append('is_active', form.is_active ? 'true' : 'false');
    if (iconFile) {
      data.append('icon_image', iconFile);
    }
    return data;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const payload = buildFormData();
      if (editing) {
        await api.admin.badges.update(editing.id, payload);
      } else {
        await api.admin.badges.create(payload);
      }
      setShowModal(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  async function handleDelete(badge: Badge) {
    if (!confirm(`Удалить бейдж «${badge.title}»?`)) return;
    try {
      await api.admin.badges.delete(badge.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">Бейджи</h1>
      {error && <div className="error-banner">{error}</div>}

      <div className="admin-actions">
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          + Добавить бейдж
        </button>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Иконка</th>
                <th>Название</th>
                <th>Уровень</th>
                <th className="col-hide-mobile">Тип</th>
                <th className="col-hide-mobile">Условие</th>
                <th className="col-hide-mobile">Активен</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {badges.map((badge) => (
                <tr key={badge.id}>
                  <td>
                    <BadgeIconPreview badge={badge} />
                  </td>
                  <td>{badge.title}</td>
                  <td>
                    <span className={`badge-level-pill badge-level-${badge.level || 'bronze'}`}>
                      {levelLabel(badge.level || 'bronze')}
                    </span>
                  </td>
                  <td className="col-hide-mobile">{badge.badge_type}</td>
                  <td className="col-hide-mobile">{conditionLabel(badge)}</td>
                  <td className="col-hide-mobile">{badge.is_active ? 'Да' : 'Нет'}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary btn-compact mr-sm"
                      onClick={() => openEdit(badge)}
                    >
                      Изменить
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger btn-compact"
                      onClick={() => void handleDelete(badge)}
                    >
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
            <h2>{editing ? 'Редактировать бейдж' : 'Новый бейдж'}</h2>
            <form onSubmit={(e) => void handleSubmit(e)}>
              <div className="form-group">
                <label>Название</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Иконка (файл PNG/JPG/SVG)</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setIconFile(e.target.files?.[0] ?? null)}
                />
                {editing?.icon_url && !iconFile && (
                  <div className="mt-sm">
                    Текущая:{' '}
                    {editing.icon_url.startsWith('http') ? (
                      <img src={editing.icon_url} alt="" className="badge-icon-sm" />
                    ) : (
                      editing.icon_url
                    )}
                  </div>
                )}
              </div>
              <div className="form-group">
                <label>Иконка (emoji или URL, если без файла)</label>
                <input
                  value={form.icon}
                  onChange={(e) => setForm({ ...form, icon: e.target.value })}
                  placeholder="🏆 или https://..."
                />
              </div>
              <div className="form-group">
                <label>Тип бейджа</label>
                <select
                  value={form.badge_type}
                  onChange={(e) => setForm({ ...form, badge_type: e.target.value })}
                >
                  {BADGE_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Уровень</label>
                <select
                  value={form.level}
                  onChange={(e) => setForm({ ...form, level: e.target.value })}
                >
                  {BADGE_LEVELS.map((l) => (
                    <option key={l.value} value={l.value}>{l.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Ключ условия (condition_key)</label>
                <input
                  value={form.condition_key}
                  onChange={(e) => setForm({ ...form, condition_key: e.target.value })}
                  placeholder="tasks_completed, project_completed, ..."
                />
              </div>
              <div className="form-group">
                <label>Условие (legacy condition_type)</label>
                <select
                  value={form.condition_type}
                  onChange={(e) => setForm({ ...form, condition_type: e.target.value })}
                >
                  {CONDITION_TYPES.map((t) => (
                    <option key={t.value || 'none'} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Значение условия</label>
                <input
                  type="number"
                  value={form.condition_value}
                  onChange={(e) => setForm({ ...form, condition_value: e.target.value })}
                  min={0}
                />
              </div>
              <div className="form-group">
                <label>Параметры условия (JSON)</label>
                <textarea
                  value={form.condition_params}
                  onChange={(e) => setForm({ ...form, condition_params: e.target.value })}
                  rows={3}
                  placeholder='{"task_slug": "print_hello"}'
                />
              </div>
              <div className="form-group">
                <label>Курс (опционально)</label>
                <select
                  value={form.course_id}
                  onChange={(e) => setForm({ ...form, course_id: e.target.value })}
                >
                  <option value="">—</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  />
                  {' '}Активен
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn btn-primary">Сохранить</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
