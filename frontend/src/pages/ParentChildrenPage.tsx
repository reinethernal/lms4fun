import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import type { ChildUser } from '@/api/types';
import { Loading } from '@/components/Loading';

const emptyCreateForm = {
  username: '',
  password: '',
  display_name: '',
};

export function ParentChildrenPage() {
  const [children, setChildren] = useState<ChildUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [passwordChildId, setPasswordChildId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');

  async function load() {
    try {
      setChildren(await api.parent.children.list());
    } catch {
      setError('Не удалось загрузить список детей');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.parent.children.create({
        username: createForm.username,
        password: createForm.password,
        display_name: createForm.display_name || createForm.username,
      });
      setCreateForm(emptyCreateForm);
      setSuccess('Аккаунт ребёнка создан.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать аккаунт');
    }
  }

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault();
    if (!passwordChildId || !newPassword) return;
    setError('');
    setSuccess('');
    try {
      await api.parent.children.setPassword(passwordChildId, newPassword);
      setNewPassword('');
      setPasswordChildId(null);
      setSuccess('Пароль обновлён.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сменить пароль');
    }
  }

  if (loading) return <Loading />;

  return (
    <div>
      <p>
        <Link to="/">← Назад в кабинет</Link>
      </p>
      <h1 className="page-title">Мои дети</h1>
      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <div className="card mb-lg">
        <h2>Добавить ребёнка</h2>
        <form onSubmit={(e) => void handleCreate(e)} className="mt-md">
          <div className="form-group">
            <label>Логин</label>
            <input
              value={createForm.username}
              onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Имя</label>
            <input
              value={createForm.display_name}
              onChange={(e) => setCreateForm({ ...createForm, display_name: e.target.value })}
              placeholder="Как отображать в кабинете"
            />
          </div>
          <div className="form-group">
            <label>Пароль</label>
            <input
              type="password"
              value={createForm.password}
              onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              minLength={6}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary">Создать аккаунт</button>
        </form>
      </div>

      <div className="card">
        <h2>Привязанные ученики</h2>
        {children.length === 0 ? (
          <p className="text-muted mt-sm">Пока нет детей.</p>
        ) : (
          <div className="table-wrap mt-md">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Имя</th>
                  <th className="col-hide-mobile">Логин</th>
                  <th className="col-hide-mobile">Последний вход</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {children.map((child) => (
                  <tr key={child.id}>
                    <td>{child.display_name || child.username}</td>
                    <td className="col-hide-mobile">{child.username}</td>
                    <td className="col-hide-mobile">
                      {child.last_login
                        ? new Date(child.last_login).toLocaleString('ru-RU')
                        : '—'}
                    </td>
                    <td>
                      <Link
                        to={`/students/${child.id}`}
                        className="btn btn-secondary btn-compact mr-sm"
                      >
                        Профиль
                      </Link>
                      <button
                        type="button"
                        className="btn btn-secondary btn-compact"
                        onClick={() => {
                          setPasswordChildId(child.id);
                          setNewPassword('');
                        }}
                      >
                        Сменить пароль
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {passwordChildId !== null && (
        <div className="modal-backdrop" onClick={() => setPasswordChildId(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Сменить пароль</h2>
            <form onSubmit={(e) => void handlePasswordChange(e)}>
              <div className="form-group">
                <label>Новый пароль</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={6}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setPasswordChildId(null)}>
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
