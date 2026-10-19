import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, isParentRole } from '@/api/client';
import type { Course, UserBadge, UserProgress } from '@/api/types';
import { Loading } from '@/components/Loading';
import { useAuth } from '@/context/AuthContext';
import { ParentDashboardPage } from '@/pages/ParentDashboardPage';

export function DashboardPage() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [progress, setProgress] = useState<UserProgress[]>([]);
  const [recentBadges, setRecentBadges] = useState<UserBadge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    void (async () => {
      try {
        const [coursesData, progressData, profileData] = await Promise.all([
          api.courses.list(),
          api.progress.me(),
          api.profile.me().catch(() => null),
        ]);
        setCourses(coursesData);
        setProgress(progressData);
        setRecentBadges(profileData?.badges.slice(0, 3) ?? []);
      } catch {
        setError('Не удалось загрузить данные');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const totalXp = useMemo(
    () => progress.reduce((sum, p) => sum + p.xp_earned, 0),
    [progress],
  );

  const tasksCompleted = useMemo(
    () => progress.reduce((sum, p) => sum + p.tasks_completed, 0),
    [progress],
  );

  const lessonsCompleted = useMemo(
    () => progress.reduce((sum, p) => sum + p.lessons_completed, 0),
    [progress],
  );

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

  if (user && isParentRole(user.role)) {
    return <ParentDashboardPage />;
  }

  if (loading) return <Loading />;

  return (
    <div>
      <div className="page-header-row">
        <h1 className="page-title">
          Привет, {user?.display_name || user?.username}!
        </h1>
        <Link to="/profile" className="btn btn-secondary">
          Мой профиль
        </Link>
      </div>

      {error && <div className="error-banner">{error}</div>}

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
        <div className="stat-card">
          <div className="stat-value">{courses.length}</div>
          <div className="stat-label">Курсов доступно</div>
        </div>
      </div>

      {recentBadges.length > 0 && (
        <>
          <h2>Последние бейджи</h2>
          <div className="flex-wrap-gap-lg mt-sm">
            {recentBadges.map((ub) => (
              <span key={ub.id} className="badge" title={ub.badge.description}>
                {ub.badge.icon_url || ub.badge.icon || '🏅'} {ub.badge.title}
              </span>
            ))}
            <Link to="/profile" className="text-sm">
              Все бейджи →
            </Link>
          </div>
        </>
      )}

      <h2 className="mt-xl">Мои курсы</h2>
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
                  {course.primary_language && (
                    <span className="badge">{course.primary_language.name}</span>
                  )}
                  <span className="badge">{course.level}</span>
                  {cp && <span className="badge badge-success">{cp.xp_earned} XP</span>}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
