import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, isPlatformAdmin } from '@/api/client';
import type { AdminSubmissionDetail, AdminTask, ChildUser, Course, Lesson, User } from '@/api/types';
import { Loading } from '@/components/Loading';
import { SubmissionDetailPanel } from '@/components/SubmissionDetailPanel';
import { SubmissionHistoryTable } from '@/components/SubmissionHistoryTable';
import { useAuth } from '@/context/AuthContext';

type StatusFilter = '' | 'manual_review' | 'accepted' | 'rejected';

const STATUS_TABS: { value: StatusFilter; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'manual_review', label: 'На проверке' },
  { value: 'accepted', label: 'Принято' },
  { value: 'rejected', label: 'Отклонено' },
];

function parseOptionalInt(value: string | null): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

export function AdminSubmissionsPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [submissions, setSubmissions] = useState<Awaited<ReturnType<typeof api.admin.submissions.list>>>([]);
  const [students, setStudents] = useState<(User | ChildUser)[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [tasks, setTasks] = useState<AdminTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState<AdminSubmissionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const statusFilter = (searchParams.get('status') ?? '') as StatusFilter;
  const userId = parseOptionalInt(searchParams.get('user_id'));
  const courseId = parseOptionalInt(searchParams.get('course_id'));
  const lessonId = parseOptionalInt(searchParams.get('lesson_id'));
  const taskId = parseOptionalInt(searchParams.get('task_id'));

  const showAttemptNumbers = Boolean(userId && taskId);

  const selectedStudent = useMemo(
    () => students.find((s) => s.id === userId),
    [students, userId],
  );
  const selectedTask = useMemo(
    () => tasks.find((t) => t.id === taskId),
    [tasks, taskId],
  );

  const updateParams = useCallback(
    (updates: Record<string, string | undefined>) => {
      const next = new URLSearchParams(searchParams);
      for (const [key, value] of Object.entries(updates)) {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const loadSubmissions = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setSubmissions(
        await api.admin.submissions.list({
          status: statusFilter || undefined,
          course_id: courseId,
          lesson_id: lessonId,
          user_id: userId,
          task_id: taskId,
        }),
      );
    } catch {
      setError('Не удалось загрузить список решений');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, courseId, lessonId, userId, taskId]);

  useEffect(() => {
    void loadSubmissions();
  }, [loadSubmissions]);

  useEffect(() => {
    void (async () => {
      try {
        const [coursesData, studentsData] = await Promise.all([
          api.admin.courses.list(),
          user && isPlatformAdmin(user.role)
            ? api.admin.users.list('student')
            : api.staff.students.list(),
        ]);
        setCourses(coursesData);
        setStudents(studentsData);
      } catch {
        // filters remain optional
      }
    })();
  }, [user]);

  useEffect(() => {
    if (!courseId) {
      setLessons([]);
      return;
    }
    void (async () => {
      try {
        setLessons(await api.admin.lessons.list(courseId));
      } catch {
        setLessons([]);
      }
    })();
  }, [courseId]);

  useEffect(() => {
    if (!lessonId) {
      setTasks([]);
      return;
    }
    void (async () => {
      try {
        setTasks(await api.admin.tasks.list(lessonId));
      } catch {
        setTasks([]);
      }
    })();
  }, [lessonId]);

  async function openDetail(id: number) {
    setDetailLoading(true);
    setError('');
    try {
      setDetail(await api.admin.submissions.get(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить решение');
    } finally {
      setDetailLoading(false);
    }
  }

  function handleReview(updated: AdminSubmissionDetail) {
    setDetail(updated);
    setSubmissions((prev) =>
      prev.map((s) =>
        s.id === updated.id
          ? {
              ...s,
              status: updated.status,
              xp_awarded: updated.xp_awarded,
            }
          : s,
      ),
    );
  }

  function handleRecheck(id: number) {
    setDetail(null);
    void loadSubmissions();
    void openDetail(id);
  }

  return (
    <div>
      <h1 className="page-title">Решения</h1>
      {error && <div className="error-banner">{error}</div>}
      {detailLoading && <p className="text-muted">Загрузка решения…</p>}

      <div className="submission-filters card mb-md">
        <div className="submission-filters-grid">
          <div className="form-group">
            <label htmlFor="filter-student">Ученик</label>
            <select
              id="filter-student"
              value={userId ?? ''}
              onChange={(e) =>
                updateParams({ user_id: e.target.value || undefined })
              }
            >
              <option value="">Все ученики</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name || s.username}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="filter-course">Курс</label>
            <select
              id="filter-course"
              value={courseId ?? ''}
              onChange={(e) =>
                updateParams({
                  course_id: e.target.value || undefined,
                  lesson_id: undefined,
                  task_id: undefined,
                })
              }
            >
              <option value="">Все курсы</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="filter-lesson">Урок</label>
            <select
              id="filter-lesson"
              value={lessonId ?? ''}
              disabled={!courseId}
              onChange={(e) =>
                updateParams({
                  lesson_id: e.target.value || undefined,
                  task_id: undefined,
                })
              }
            >
              <option value="">Все уроки</option>
              {lessons.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.number}. {l.title}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="filter-task">Задание</label>
            <select
              id="filter-task"
              value={taskId ?? ''}
              disabled={!lessonId}
              onChange={(e) =>
                updateParams({ task_id: e.target.value || undefined })
              }
            >
              <option value="">Все задания</option>
              {tasks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
          </div>
        </div>
        {(userId || taskId) && (
          <button
            type="button"
            className="btn btn-secondary btn-sm mt-sm"
            onClick={() =>
              updateParams({
                user_id: undefined,
                course_id: undefined,
                lesson_id: undefined,
                task_id: undefined,
              })
            }
          >
            Сбросить фильтры
          </button>
        )}
      </div>

      {showAttemptNumbers && selectedStudent && selectedTask && (
        <p className="hint-text mb-md">
          История: <strong>{selectedStudent.display_name || selectedStudent.username}</strong>
          {' — '}
          <strong>{selectedTask.title}</strong>
          {' · '}
          {submissions.length}{' '}
          {submissions.length === 1 ? 'попытка' : submissions.length < 5 ? 'попытки' : 'попыток'}
        </p>
      )}

      <div className="tabs-row mb-md">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value || 'all'}
            type="button"
            className={`btn btn-compact ${statusFilter === tab.value ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => updateParams({ status: tab.value || undefined })}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <Loading />
      ) : (
        <div className="card">
          <SubmissionHistoryTable
            submissions={submissions}
            showStudent={!userId}
            showAttemptNumber={showAttemptNumbers}
            onOpen={(id) => void openDetail(id)}
          />
        </div>
      )}

      {detail && (
        <SubmissionDetailPanel
          submission={detail}
          mode="staff"
          onClose={() => setDetail(null)}
          onReview={handleReview}
          onRecheck={handleRecheck}
        />
      )}
    </div>
  );
}
