import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import type { Course, Lesson } from '@/api/types';
import { Loading } from '@/components/Loading';

function LessonStatusBadge({ lesson }: { lesson: Lesson }) {
  const locked = Boolean(lesson.is_locked);
  const completed = Boolean(lesson.is_completed);
  const inReview = Boolean(lesson.is_in_review);
  if (completed) return <span className="badge badge-success">Пройден</span>;
  if (inReview) return <span className="badge badge-info">На проверке</span>;
  if (locked) return <span className="badge">Закрыт</span>;
  return <span className="badge">Доступен</span>;
}

export function CoursePage() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);

  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!courseId) return;
    void (async () => {
      try {
        const [courseData, lessonsData] = await Promise.all([
          api.courses.get(courseId),
          api.courses.lessons(courseId),
        ]);
        setCourse(courseData);
        setLessons(lessonsData.sort((a, b) => a.sort_order - b.sort_order || a.number - b.number));
      } catch {
        setError('Не удалось загрузить курс');
      } finally {
        setLoading(false);
      }
    })();
  }, [courseId]);

  if (loading) return <Loading />;
  if (error) return <div className="error-banner">{error}</div>;
  if (!course) return <div className="error-banner">Курс не найден</div>;

  return (
    <div>
      <p>
        <Link to="/">← Назад в кабинет</Link>
      </p>
      <h1 className="page-title">{course.title}</h1>
      {course.description && (
        <p className="text-muted mb-lg">{course.description}</p>
      )}

      <h2>Уроки</h2>
      {lessons.length === 0 ? (
        <p className="text-muted">Уроки пока не добавлены.</p>
      ) : (
        <div className="card mt-md">
          <div className="table-wrap course-table-desktop">
            <table className="data-table">
              <thead>
                <tr>
                  <th>№</th>
                  <th>Название</th>
                  <th className="col-hide-mobile">Цель</th>
                  <th>XP</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {lessons.map((lesson) => {
                  const locked = Boolean(lesson.is_locked);
                  return (
                    <tr key={lesson.id} className={locked ? 'row-locked' : undefined}>
                      <td>{lesson.number}</td>
                      <td>{lesson.title}</td>
                      <td className="col-hide-mobile text-muted">{lesson.goal}</td>
                      <td>{lesson.max_xp}</td>
                      <td>
                        <LessonStatusBadge lesson={lesson} />
                      </td>
                      <td>
                        {locked ? (
                          <button
                            type="button"
                            className="btn btn-secondary btn-compact"
                            disabled
                            title="Сначала пройдите предыдущий урок"
                          >
                            Закрыт
                          </button>
                        ) : (
                          <Link to={`/lessons/${lesson.id}`} className="btn btn-secondary btn-compact">
                            Открыть
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="lesson-cards">
            {lessons.map((lesson) => {
              const locked = Boolean(lesson.is_locked);
              return (
                <div key={lesson.id} className={`lesson-card${locked ? ' row-locked' : ''}`}>
                  <div className="lesson-card-header">
                    <p className="lesson-card-title">
                      Урок {lesson.number}: {lesson.title}
                    </p>
                    <LessonStatusBadge lesson={lesson} />
                  </div>
                  {lesson.goal && <p className="lesson-card-goal">{lesson.goal}</p>}
                  <div className="lesson-card-footer">
                    <span className="badge badge-xp">{lesson.max_xp} XP</span>
                    {locked ? (
                      <button type="button" className="btn btn-secondary btn-compact" disabled>
                        Закрыт
                      </button>
                    ) : (
                      <Link to={`/lessons/${lesson.id}`} className="btn btn-secondary btn-compact">
                        Открыть
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
