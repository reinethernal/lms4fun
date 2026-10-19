import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { Group, User } from '@/api/types';
import { Loading } from '@/components/Loading';
import { StudentProfileLink } from '@/components/StudentProfileLink';

export function AdminGroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Group | null>(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    teacher_id: '' as string,
    member_ids: [] as number[],
    is_active: true,
  });

  async function load() {
    try {
      const [groupsData, usersData] = await Promise.all([
        api.admin.groups.list(),
        api.admin.users.list(),
      ]);
      setGroups(groupsData);
      setUsers(usersData);
    } catch {
      setError('Не удалось загрузить группы');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openCreate() {
    setEditing(null);
    setForm({ title: '', description: '', teacher_id: '', member_ids: [], is_active: true });
    setShowModal(true);
  }

  function openEdit(group: Group) {
    setEditing(group);
    setForm({
      title: group.title,
      description: group.description,
      teacher_id: group.teacher ? String(group.teacher.id) : '',
      member_ids: group.members.map((m) => m.id),
      is_active: group.is_active,
    });
    setShowModal(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    const payload = {
      title: form.title,
      description: form.description,
      teacher_id: form.teacher_id ? Number(form.teacher_id) : null,
      member_ids: form.member_ids,
      is_active: form.is_active,
    };
    try {
      if (editing) {
        await api.admin.groups.update(editing.id, payload);
      } else {
        await api.admin.groups.create(payload);
      }
      setShowModal(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  async function handleDelete(group: Group) {
    if (!confirm(`Удалить группу «${group.title}»?`)) return;
    try {
      await api.admin.groups.delete(group.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  }

  function toggleMember(userId: number) {
    setForm((prev) => ({
      ...prev,
      member_ids: prev.member_ids.includes(userId)
        ? prev.member_ids.filter((id) => id !== userId)
        : [...prev.member_ids, userId],
    }));
  }

  if (loading) return <Loading />;

  const teachers = users.filter((u) => ['teacher', 'admin', 'superadmin'].includes(u.role));
  const students = users.filter((u) => u.role === 'student');

  return (
    <div>
      <h1 className="page-title">Группы</h1>
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
                <th>Преподаватель</th>
                <th>Ученики</th>
                <th>Активна</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {groups.map((group) => (
                <tr key={group.id}>
                  <td className="col-hide-mobile">{group.id}</td>
                  <td>{group.title}</td>
                  <td>{group.teacher?.display_name || group.teacher?.username || '—'}</td>
                  <td>
                    {group.members.length === 0 ? (
                      '—'
                    ) : (
                      <span className="flex-wrap-gap">
                        {group.members
                          .filter((m) => m.role === 'student')
                          .map((member, index, arr) => (
                            <span key={member.id}>
                              <StudentProfileLink userId={member.id}>
                                {member.display_name || member.username}
                              </StudentProfileLink>
                              {index < arr.length - 1 ? ', ' : ''}
                            </span>
                          ))}
                      </span>
                    )}
                  </td>
                  <td>{group.is_active ? 'Да' : 'Нет'}</td>
                  <td>
                    <button type="button" className="btn btn-secondary btn-compact mr-sm" onClick={() => openEdit(group)}>
                      Изменить
                    </button>
                    <button type="button" className="btn btn-danger btn-compact" onClick={() => void handleDelete(group)}>
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
            <h2>{editing ? 'Редактировать группу' : 'Новая группа'}</h2>
            <form onSubmit={(e) => void handleSubmit(e)}>
              <div className="form-group">
                <label>Название</label>
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
              </div>
              <div className="form-group">
                <label>Преподаватель</label>
                <select value={form.teacher_id} onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}>
                  <option value="">—</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>{t.display_name || t.username}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Участники</label>
                <div className="checkbox-list-bordered checkbox-list">
                  {students.map((s) => (
                    <label key={s.id} className="checkbox-row-with-link">
                      <span>
                        <input
                          type="checkbox"
                          checked={form.member_ids.includes(s.id)}
                          onChange={() => toggleMember(s.id)}
                        />
                        {' '}{s.display_name || s.username}
                      </span>
                      <StudentProfileLink userId={s.id} className="text-sm">
                        Профиль
                      </StudentProfileLink>
                    </label>
                  ))}
                </div>
              </div>
              <div className="form-group">
                <label>
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                  {' '}Активна
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
