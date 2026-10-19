import type { AdminSubmission } from '@/api/types';

export interface TaskSubmissionGroup {
  taskId: number;
  taskTitle: string;
  lessonTitle: string;
  attempts: AdminSubmission[];
  latest: AdminSubmission;
}

export function groupSubmissionsByTask(submissions: AdminSubmission[]): TaskSubmissionGroup[] {
  const map = new Map<number, AdminSubmission[]>();
  for (const item of submissions) {
    const list = map.get(item.task.id) ?? [];
    list.push(item);
    map.set(item.task.id, list);
  }

  const groups: TaskSubmissionGroup[] = [];
  for (const [taskId, attempts] of map) {
    const sorted = [...attempts].sort((a, b) => {
      const aTime = a.submitted_at ? new Date(a.submitted_at).getTime() : 0;
      const bTime = b.submitted_at ? new Date(b.submitted_at).getTime() : 0;
      return bTime - aTime;
    });
    const latest = sorted[0];
    groups.push({
      taskId,
      taskTitle: latest.task.title,
      lessonTitle: latest.task.lesson_title ?? '',
      attempts: sorted,
      latest,
    });
  }

  return groups.sort((a, b) => {
    const aTime = a.latest.submitted_at ? new Date(a.latest.submitted_at).getTime() : 0;
    const bTime = b.latest.submitted_at ? new Date(b.latest.submitted_at).getTime() : 0;
    return bTime - aTime;
  });
}
