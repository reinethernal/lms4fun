import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { ChildUser, StaffParent } from '@/api/types';
import { Loading } from '@/components/Loading';
import { StudentProfileLink } from '@/components/StudentProfileLink';

export function AdminParentsPage() {
  const [parents, setParents] = useState<StaffParent[]>([]);
  const [students, setStudents] = useState<ChildUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editingParent, setEditingParent] = useState<StaffParent | null>(null);
  const [selectedChildIds, setSelectedChildIds] = useState<number[]>([]);

  async function load() {
    try {
      const [parentsData, studentsData] = await Promise.all([
        api.staff.parents.list(),
        api.staff.students.list(),
      ]);
      setParents(parentsData);
      setStudents(studentsData);
    } catch {
      setError('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openEdit(parent: StaffParent) {
    setEditingParent(parent);
    setSelectedChildIds(parent.children.map((c) => c.id));
    setError('');
    setSuccess('');
  }

  function toggleChild(childId: number) {
    setSelectedChildIds((prev) =>
      prev.includes(childId) ? prev.filter((id) => id !== childId) : [...prev, childId],
    );
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!editingParent) return;
    setError('');
    setSuccess('');
    try {
      await api.staff.parents.setChildren(editingParent.id, selectedChildIds);
      setEditingParent(null);
      setSuccess('Привязка детей обновлена.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  if (loading) return <Loading />;

  return (
    <div>
      <h1 className="page-title">Родители и дети</h1>
      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Родитель</th>
                <th className="col-hide-mobile">Логин</th>
                <th>Дети</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {parents.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center-muted">
                    Родителей пока нет
                  </td>
                </tr>
              ) : (
                parents.map((parent) => (
                  <tr key={parent.id}>
                    <td>{parent.display_name || parent.username}</td>
                    <td className="col-hide-mobile">{parent.username}</td>
                    <td>
                      {parent.children.length === 0 ? (
                        '—'
                      ) : (
                        <span className="flex-wrap-gap">
                          {parent.children.map((child, index) => (
                            <span key={child.id}>
                              <StudentProfileLink userId={child.id}>
                                {child.display_name || child.username}
                              </StudentProfileLink>
                              {index < parent.children.length - 1 ? ', ' : ''}
                            </span>
                          ))}
                        </span>
                      )}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary btn-compact"
                        onClick={() => openEdit(parent)}
                      >
                        Привязать детей
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {editingParent && (
        <div className="modal-backdrop" onClick={() => setEditingParent(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Дети: {editingParent.display_name || editingParent.username}</h2>
            <form onSubmit={(e) => void handleSave(e)}>
              <div className="form-group">
                <label>Выберите учеников</label>
                <div className="scroll-y-sm checkbox-list">
                  {students.length === 0 ? (
                    <p className="text-muted">Нет доступных учеников</p>
                  ) : (
                    students.map((student) => (
                      <label key={student.id} className="checkbox-row-with-link">
                        <span>
                          <input
                            type="checkbox"
                            checked={selectedChildIds.includes(student.id)}
                            onChange={() => toggleChild(student.id)}
                          />
                          {' '}
                          {student.display_name || student.username} ({student.username})
                        </span>
                        <StudentProfileLink userId={student.id} className="text-sm">
                          Профиль
                        </StudentProfileLink>
                      </label>
                    ))
                  )}
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingParent(null)}>
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
