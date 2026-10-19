import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import type { ChildUser, User, UserRole } from '@/api/types';
import { Loading } from '@/components/Loading';
import { StudentProfileLink } from '@/components/StudentProfileLink';

const ROLES: { value: UserRole; label: string }[] = [
  { value: 'student', label: 'Ученик' },
  { value: 'teacher', label: 'Преподаватель' },
  { value: 'admin', label: 'Администратор' },
  { value: 'superadmin', label: 'Суперадмин' },
  { value: 'parent', label: 'Родитель' },
];

const roleLabel = (role: string) => ROLES.find((r) => r.value === role)?.label ?? role;

export function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [students, setStudents] = useState<ChildUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [resetTarget, setResetTarget] = useState<User | null>(null);
  const [resetIncludeSubmissions, setResetIncludeSubmissions] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    display_name: '',
    role: 'student' as UserRole,
    is_active: true,
    child_ids: [] as number[],
  });

  async function load() {
    try {
      const [usersData, studentsData] = await Promise.all([
        api.admin.users.list(),
        api.staff.students.list(),
      ]);
      setUsers(usersData);
      setStudents(studentsData);
    } catch {
      setError('Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function studentEmail(username: string) {
    return username.trim() ? `${username.trim()}@localhost` : '';
  }

  function openCreate() {
    setEditing(null);
    setForm({
      username: '',
      email: '',
      password: '',
      display_name: '',
      role: 'student',
      is_active: true,
      child_ids: [],
    });
    setShowModal(true);
  }

  function updateForm(patch: Partial<typeof form>) {
    setForm((prev) => {
      const next = { ...prev, ...patch };
      if (
        next.role === 'student' &&
        !editing &&
        (patch.username !== undefined || patch.role !== undefined)
      ) {
        const suggested = studentEmail(next.username);
        if (!prev.email || prev.email === studentEmail(prev.username)) {
          next.email = suggested;
        }
      }
      return next;
    });
  }

  function openEdit(user: User) {
    setEditing(user);
    setForm({
      username: user.username,
      email: user.email,
      password: '',
      display_name: user.display_name,
      role: user.role,
      is_active: user.is_active,
      child_ids: user.children?.map((c) => c.id) ?? [],
    });
    setShowModal(true);
  }

  function toggleChild(childId: number) {
    setForm((prev) => ({
      ...prev,
      child_ids: prev.child_ids.includes(childId)
        ? prev.child_ids.filter((id) => id !== childId)
        : [...prev.child_ids, childId],
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      if (editing) {
        const payload: Partial<User> & { password?: string; child_ids?: number[] } = {
          username: form.username,
          email: form.email,
          display_name: form.display_name,
          role: form.role,
          is_active: form.is_active,
        };
        if (form.password) payload.password = form.password;
        if (form.role === 'parent') payload.child_ids = form.child_ids;
        await api.admin.users.update(editing.id, payload);
      } else {
        await api.admin.users.create({
          username: form.username,
          email: form.email,
          password: form.password,
          display_name: form.display_name,
          role: form.role,
          is_active: form.is_active,
        });
      }
      setShowModal(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  async function handleDelete(user: User) {
    if (!confirm(`Удалить пользователя ${user.username}?`)) return;
    try {
      await api.admin.users.delete(user.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  function openResetStats(user: User) {
    setResetTarget(user);
    setResetIncludeSubmissions(false);
  }

  async function handleResetStats() {
    if (!resetTarget) return;
    setResetBusy(true);
    setError('');
    try {
      const result = await api.admin.users.resetStatistics(resetTarget.id, {
        include_submissions: resetIncludeSubmissions,
      });
      setResetTarget(null);
      await load();
      setError('');
      alert(result.detail || 'Статистика сброшена');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сброса статистики');
    } finally {
      setResetBusy(false);
    }
  }

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">Пользователи</h1>
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
                <th>Логин</th>
                <th>Имя</th>
                <th>Роль</th>
                <th>Активен</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="col-hide-mobile">{user.id}</td>
                  <td>
                    {user.role === 'student' ? (
                      <StudentProfileLink userId={user.id}>{user.username}</StudentProfileLink>
                    ) : (
                      user.username
                    )}
                  </td>
                  <td>
                    {user.role === 'student' ? (
                      <StudentProfileLink userId={user.id}>
                        {user.display_name || user.username}
                      </StudentProfileLink>
                    ) : (
                      user.display_name || '—'
                    )}
                  </td>
                  <td>{roleLabel(user.role)}</td>
                  <td>{user.is_active ? 'Да' : 'Нет'}</td>
                  <td>
                    <button type="button" className="btn btn-secondary btn-compact mr-sm" onClick={() => openEdit(user)}>
                      Изменить
                    </button>
                    {user.role === 'student' && (
                      <>
                        <Link
                          to={`/students/${user.id}`}
                          className="btn btn-secondary btn-compact mr-sm"
                        >
                          Профиль
                        </Link>
                        <button
                          type="button"
                          className="btn btn-secondary btn-compact mr-sm"
                          onClick={() => openResetStats(user)}
                        >
                          Сбросить статистику
                        </button>
                      </>
                    )}
                    <button type="button" className="btn btn-danger btn-compact" onClick={() => void handleDelete(user)}>
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {resetTarget && (
        <div className="modal-backdrop" onClick={() => !resetBusy && setResetTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Сброс статистики</h2>
            <p>
              Сбросить XP, бейджи и прогресс для ученика{' '}
              <strong>{resetTarget.display_name || resetTarget.username}</strong>?
            </p>
            <label>
              <input
                type="checkbox"
                checked={resetIncludeSubmissions}
                onChange={(e) => setResetIncludeSubmissions(e.target.checked)}
                disabled={resetBusy}
              />
              {' '}Также удалить решения и запуски кода (ученик начнёт курс с нуля)
            </label>
            <div className="modal-actions mt-md">
              <button type="button" className="btn btn-secondary" onClick={() => setResetTarget(null)} disabled={resetBusy}>
                Отмена
              </button>
              <button type="button" className="btn btn-danger" onClick={() => void handleResetStats()} disabled={resetBusy}>
                Сбросить
              </button>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editing ? 'Редактировать' : 'Новый пользователь'}</h2>
            <form onSubmit={(e) => void handleSubmit(e)}>
              <div className="form-group">
                <label>Логин</label>
                <input value={form.username} onChange={(e) => updateForm({ username: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={form.email} onChange={(e) => updateForm({ email: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>{editing ? 'Новый пароль (необязательно)' : 'Пароль'}</label>
                <input type="password" value={form.password} onChange={(e) => updateForm({ password: e.target.value })} required={!editing} minLength={6} />
              </div>
              <div className="form-group">
                <label>Отображаемое имя</label>
                <input value={form.display_name} onChange={(e) => updateForm({ display_name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Роль</label>
                <select value={form.role} onChange={(e) => updateForm({ role: e.target.value as UserRole })}>
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>
              {form.role === 'parent' && editing && (
                <div className="form-group">
                  <label>Привязанные дети</label>
                  <div className="scroll-y-md checkbox-list">
                    {students.map((student) => (
                      <label key={student.id}>
                        <input
                          type="checkbox"
                          checked={form.child_ids.includes(student.id)}
                          onChange={() => toggleChild(student.id)}
                        />
                        {' '}
                        {student.display_name || student.username}
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <div className="form-group">
                <label>
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                  {' '}Активен
                </label>
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
