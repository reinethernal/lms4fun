import type { AdminSubmission, AdminSubmissionDetail } from '@/api/types';
import { StudentProfileLink } from '@/components/StudentProfileLink';
import { statusBadgeClass, statusLabelRu } from '@/utils/submissionStatus';

export interface SubmissionWithAttempt extends AdminSubmission {
  attemptNumber: number;
}

export function assignAttemptNumbers(submissions: AdminSubmission[]): SubmissionWithAttempt[] {
  const byTask = new Map<number, AdminSubmission[]>();
  for (const item of submissions) {
    const list = byTask.get(item.task.id) ?? [];
    list.push(item);
    byTask.set(item.task.id, list);
  }

  const attemptMap = new Map<number, number>();
  for (const items of byTask.values()) {
    const sorted = [...items].sort((a, b) => {
      const aTime = a.submitted_at ? new Date(a.submitted_at).getTime() : 0;
      const bTime = b.submitted_at ? new Date(b.submitted_at).getTime() : 0;
      return aTime - bTime;
    });
    sorted.forEach((item, index) => {
      attemptMap.set(item.id, index + 1);
    });
  }

  return submissions.map((item) => ({
    ...item,
    attemptNumber: attemptMap.get(item.id) ?? 1,
  }));
}

interface SubmissionHistoryTableProps {
  submissions: AdminSubmission[];
  showStudent?: boolean;
  showAttemptNumber?: boolean;
  onOpen: (id: number) => void;
}

export function SubmissionHistoryTable({
  submissions,
  showStudent = true,
  showAttemptNumber = true,
  onOpen,
}: SubmissionHistoryTableProps) {
  const rows = assignAttemptNumbers(submissions);

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {showAttemptNumber && <th>№</th>}
            <th>Дата</th>
            {showStudent && <th>Ученик</th>}
            <th>Задание</th>
            <th>Статус</th>
            <th className="col-hide-mobile">XP</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={5 + (showAttemptNumber ? 1 : 0) + (showStudent ? 1 : 0)}
                className="text-center-muted"
              >
                Решений пока нет
              </td>
            </tr>
          ) : (
            rows.map((s) => (
              <tr key={s.id}>
                {showAttemptNumber && (
                  <td className="submission-attempt-num">{s.attemptNumber}</td>
                )}
                <td>{s.submitted_at ? new Date(s.submitted_at).toLocaleString('ru-RU') : '—'}</td>
                {showStudent && (
                  <td>
                    <StudentProfileLink userId={s.user.id}>
                      {s.user.display_name || s.user.username}
                    </StudentProfileLink>
                  </td>
                )}
                <td>
                  {s.task.title}
                  {s.task.lesson_title && (
                    <span className="hint-text block">{s.task.lesson_title}</span>
                  )}
                </td>
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
                    onClick={() => onOpen(s.id)}
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
  );
}

export type { AdminSubmissionDetail };
