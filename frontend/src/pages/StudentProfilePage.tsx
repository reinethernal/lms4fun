import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import type { AdminSubmission, AdminSubmissionDetail, Course, StudentProfile } from '@/api/types';
import { Loading } from '@/components/Loading';
import { ProfileHeader } from '@/components/ProfileHeader';
import { ProfileSettingsForm } from '@/components/ProfileSettingsForm';
import { StudentBadgesPanel } from '@/components/StudentBadgesPanel';
import { SubmissionDetailPanel } from '@/components/SubmissionDetailPanel';
import { useAuth } from '@/context/AuthContext';
import { statusBadgeClass, statusLabelRu } from '@/utils/submissionStatus';
import { groupSubmissionsByTask } from '@/utils/submissionGroups';

export function StudentProfilePage() {
  const { user: currentUser, refresh } = useAuth();
  const { userId: userIdParam } = useParams<{ userId?: string }>();
  const navigate = useNavigate();
  const targetUserId = userIdParam ? Number(userIdParam) : null;
  const isSelfProfile = !targetUserId || targetUserId === currentUser?.id;

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [submissionHistory, setSubmissionHistory] = useState<AdminSubmission[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [detail, setDetail] = useState<AdminSubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = isSelfProfile
        ? await api.profile.me()
        : await api.students.profile(targetUserId!);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль');
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [isSelfProfile, targetUserId]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (profile?.user.role !== 'student') return;
    void (async () => {
      try {
        setCourses(await api.courses.list());
      } catch {
        // optional for course cards
      }
    })();
  }, [profile?.user.role]);

  const showStaffHistory = Boolean(
    profile?.user.role === 'student'
    && profile.permissions.can_view_submissions
    && !isSelfProfile
    && targetUserId,
  );

  useEffect(() => {
    if (!showStaffHistory || !targetUserId) {
      setSubmissionHistory([]);
      return;
    }
    void (async () => {
      setHistoryLoading(true);
      try {
        setSubmissionHistory(await api.students.submissions.list(targetUserId));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить историю решений');
        setSubmissionHistory([]);
      } finally {
        setHistoryLoading(false);
      }
    })();
  }, [showStaffHistory, targetUserId]);

  const groupedSubmissions = useMemo(
    () => groupSubmissionsByTask(submissionHistory),
    [submissionHistory],
  );

  const progressByCourse = useMemo(() => {
    const map = new Map<number, StudentProfile['progress'][0]>();
    for (const p of profile?.progress ?? []) {
      const existing = map.get(p.course);
      if (!existing || p.xp_earned > existing.xp_earned) {
        map.set(p.course, p);
      }
    }
    return map;
  }, [profile?.progress]);

  async function openSubmission(id: number) {
    try {
      setDetail(await api.submissions.get(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить решение');
    }
  }

  async function handleProfileUpdated() {
    await refresh();
    await loadProfile();
  }

  if (loading) return <Loading />;
  if (!profile) {
    return (
      <div>
        <div className="error-banner">{error || 'Профиль не найден'}</div>
        <button type="button" className="btn btn-secondary mt-md" onClick={() => navigate(-1)}>
          Назад
        </button>
      </div>
    );
  }

  const { user, stats, permissions } = profile;
  const isStudentProfile = user.role === 'student';
  const badgeMode = permissions.can_manage_badges ? 'manage' : 'readonly';
  const showSettings = isSelfProfile && permissions.can_edit;

  return (
    <div>
      {!isSelfProfile && (
        <button type="button" className="btn btn-secondary btn-compact mb-md" onClick={() => navigate(-1)}>
          ← Назад
        </button>
      )}

      {error && <div className="error-banner">{error}</div>}

      <ProfileHeader
        user={user}
        subtitle={isStudentProfile ? 'Профиль ученика' : undefined}
      />

      {isStudentProfile && (
        <div className="stats-row mt-lg">
          <div className="stat-card">
            <div className="stat-value">{stats.total_xp}</div>
            <div className="stat-label">Всего XP</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.lessons_completed}</div>
            <div className="stat-label">Уроков пройдено</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.tasks_completed}</div>
            <div className="stat-label">Заданий выполнено</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.badges_count}</div>
            <div className="stat-label">Бейджей</div>
          </div>
          {stats.rank !== null && (
            <div className="stat-card">
              <div className="stat-value">#{stats.rank}</div>
              <div className="stat-label">Место в рейтинге</div>
            </div>
          )}
        </div>
      )}

      {isStudentProfile && courses.length > 0 && (
        <>
          <h2 className="mt-xl">Прогресс по курсам</h2>
          <div className="card-grid mt-md">
            {courses.map((course) => {
              const cp = progressByCourse.get(course.id);
              return (
                <Link key={course.id} to={`/courses/${course.id}`} className="card card-link">
                  <h3>{course.title}</h3>
                  <p className="text-muted text-sm">{course.description || 'Без описания'}</p>
                  <div className="flex-wrap-gap mt-sm">
                    {cp && <span className="badge badge-success">{cp.xp_earned} XP</span>}
                    {cp && <span className="badge">{cp.lessons_completed} уроков</span>}
                  </div>
                </Link>
              );
            })}
          </div>
        </>
      )}

      {isStudentProfile && (
        <>
          <h2 className="mt-xl">Бейджи</h2>
          <StudentBadgesPanel
            userId={user.id}
            mode={badgeMode}
            initialBadges={profile.badges}
            onBadgesChange={() => void loadProfile()}
          />
        </>
      )}

      {showStaffHistory && (
        <>
          <h2 className="mt-xl">История решений</h2>
          {historyLoading ? (
            <Loading />
          ) : (
            <div className="card mt-md">
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Задание</th>
                      <th>Урок</th>
                      <th>Попыток</th>
                      <th>Последний статус</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupedSubmissions.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="text-center-muted">
                          Решений пока нет
                        </td>
                      </tr>
                    ) : (
                      groupedSubmissions.map((group) => (
                        <tr key={group.taskId}>
                          <td>{group.taskTitle}</td>
                          <td>{group.lessonTitle || '—'}</td>
                          <td>{group.attempts.length}</td>
                          <td>
                            <span className={`badge ${statusBadgeClass(group.latest.status)}`}>
                              {statusLabelRu(group.latest.status)}
                            </span>
                          </td>
                          <td>
                            <Link
                              to={`/admin/submissions?user_id=${user.id}&task_id=${group.taskId}`}
                              className="btn btn-secondary btn-compact"
                            >
                              Все попытки
                            </Link>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {isStudentProfile && permissions.can_view_submissions && isSelfProfile && (
        <>
          <h2 className="mt-xl">Последние решения</h2>
          <div className="card mt-md">
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th>Задание</th>
                    <th>Статус</th>
                    <th className="col-hide-mobile">XP</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {profile.recent_submissions.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center-muted">
                        Решений пока нет
                      </td>
                    </tr>
                  ) : (
                    profile.recent_submissions.map((s) => (
                      <tr key={s.id}>
                        <td>
                          {s.submitted_at
                            ? new Date(s.submitted_at).toLocaleString('ru-RU')
                            : '—'}
                        </td>
                        <td>{s.task.title}</td>
                        <td>
                          <span className={`badge ${statusBadgeClass(s.status)}`}>
                            {statusLabelRu(s.status)}
                          </span>
                        </td>
                        <td className="col-hide-mobile">{s.xp_awarded}</td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-secondary btn-compact"
                            onClick={() => void openSubmission(s.id)}
                          >
                            Посмотреть
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {showSettings && (
        <div className="mt-xl">
          <ProfileSettingsForm user={user} onUpdated={() => void handleProfileUpdated()} />
        </div>
      )}

      {detail && (
        <SubmissionDetailPanel
          submission={detail}
          mode={showStaffHistory ? 'staff' : 'readonly'}
          onClose={() => setDetail(null)}
        />
      )}
    </div>
  );
}
