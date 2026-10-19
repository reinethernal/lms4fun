import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import type { ChildUser, Course, UserProgress } from '@/api/types';
import { Loading } from '@/components/Loading';

export function ParentDashboardPage() {
  const [children, setChildren] = useState<ChildUser[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [progress, setProgress] = useState<UserProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [childLoading, setChildLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    void (async () => {
      try {
        const [childrenData, coursesData] = await Promise.all([
          api.parent.children.list(),
          api.courses.list(),
        ]);
        setChildren(childrenData);
        setCourses(coursesData);
        if (childrenData.length > 0) {
          setSelectedChildId(childrenData[0].id);
        }
      } catch {
        setError('Не удалось загрузить данные');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedChildId) {
      setProgress([]);
      return;
    }
    void (async () => {
      setChildLoading(true);
      try {
        setProgress(await api.parent.children.progress(selectedChildId));
      } catch {
        setError('Не удалось загрузить данные ученика');
      } finally {
        setChildLoading(false);
      }
    })();
  }, [selectedChildId]);

  const selectedChild = children.find((c) => c.id === selectedChildId) ?? null;

  const totalXp = useMemo(() => progress.reduce((sum, p) => sum + p.xp_earned, 0), [progress]);
  const tasksCompleted = useMemo(() => progress.reduce((sum, p) => sum + p.tasks_completed, 0), [progress]);
  const lessonsCompleted = useMemo(() => progress.reduce((sum, p) => sum + p.lessons_completed, 0), [progress]);

  const progressByCourse = useMemo(() => {
    const map = new Map<number, UserProgress>();
    for (const p of progress) {
      const existing = map.get(p.course);
      if (!existing || p.xp_earned > existing.xp_earned) {
        map.set(p.course, p);
      }
    }
    return map;
  }, [progress]);

  if (loading) return <Loading />;

  return (
    <div>
      <div className="page-header-row">
        <h1 className="page-title">Родительский кабинет</h1>
        <div className="flex-wrap-gap">
          <Link to="/profile" className="btn btn-secondary">Мой профиль</Link>
          <Link to="/children" className="btn btn-secondary">Управление детьми</Link>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {children.length === 0 ? (
        <div className="card mt-lg">
          <p>У вас пока нет привязанных учеников.</p>
          <Link to="/children" className="btn btn-primary mt-sm">
            Добавить ребёнка
          </Link>
        </div>
      ) : (
        <>
          <div className="form-group form-narrow">
            <label>Ученик</label>
            <select
              value={selectedChildId ?? ''}
              onChange={(e) => setSelectedChildId(Number(e.target.value))}
            >
              {children.map((child) => (
                <option key={child.id} value={child.id}>
                  {child.display_name || child.username}
                </option>
              ))}
            </select>
          </div>

          {selectedChild && selectedChildId !== null && (
            <div className="page-header-row mt-sm">
              <p className="text-muted text-sm">
                Логин: {selectedChild.username}
                {selectedChild.last_login && (
                  <> · Последний вход: {new Date(selectedChild.last_login).toLocaleString('ru-RU')}</>
                )}
              </p>
              <Link to={`/students/${selectedChildId}`} className="btn btn-primary btn-compact">
                Профиль ребёнка
              </Link>
            </div>
          )}

          {childLoading ? (
            <Loading />
          ) : (
            <>
              <div className="stats-row">
                <div className="stat-card">
                  <div className="stat-value">{totalXp}</div>
                  <div className="stat-label">Всего XP</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{lessonsCompleted}</div>
                  <div className="stat-label">Уроков пройдено</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{tasksCompleted}</div>
                  <div className="stat-label">Заданий выполнено</div>
                </div>
              </div>

              <h2>Курсы</h2>
              {courses.length === 0 ? (
                <p className="text-muted">Курсы пока не назначены.</p>
              ) : (
                <div className="card-grid mt-md">
                  {courses.map((course) => {
                    const cp = progressByCourse.get(course.id);
                    return (
                      <Link key={course.id} to={`/courses/${course.id}`} className="card card-link">
                        <h3>{course.title}</h3>
                        <p className="text-muted text-sm">
                          {course.description || 'Без описания'}
                        </p>
                        <div className="flex-wrap-gap mt-sm">
                          {cp && <span className="badge badge-success">{cp.xp_earned} XP</span>}
                          {cp && <span className="badge">{cp.lessons_completed} уроков</span>}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}

              {selectedChildId !== null && (
                <p className="text-muted mt-xl">
                  Бейджи, решения и подробная статистика — в{' '}
                  <Link to={`/students/${selectedChildId}`}>профиле ребёнка</Link>.
                </p>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
