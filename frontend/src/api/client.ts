import type {
  AdminSubmission,
  AdminSubmissionDetail,
  Badge,
  ChildUser,
  CodeRunResult,
  Course,
  Group,
  LeaderboardEntry,
  Lesson,
  ImportJob,
  StaffParent,
  SubmissionResult,
  Task,
  User,
  UserBadge,
  UserProgress,
  ProgrammingLanguage,
  AdminTask,
  ProfileUpdatePayload,
  StudentProfile,
  TelegramLinkCode,
  TelegramBotSettings,
  TelegramBotSettingsUpdate,
  TelegramStatus,
} from './types';

const API_BASE = '/api';

function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export class ApiClientError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.data = data;
  }
}

export function formatApiError(data: unknown): string {
  if (typeof data === 'string' && data) return data;
  if (typeof data !== 'object' || data === null) return '';
  const obj = data as Record<string, unknown>;
  if ('detail' in obj) {
    const detail = obj.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map(String).join(' ');
  }
  const parts: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    if (key === 'non_field_errors' && Array.isArray(value)) {
      parts.push(value.map(String).join(' '));
    } else if (Array.isArray(value)) {
      parts.push(`${key}: ${value.map(String).join(' ')}`);
    } else if (typeof value === 'string') {
      parts.push(`${key}: ${value}`);
    }
  }
  return parts.join('; ');
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (options.method ?? 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf) {
      headers.set('X-CSRFToken', csrf);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = formatApiError(data) || `Ошибка запроса (${response.status})`;
    throw new ApiClientError(message, response.status, data);
  }

  return data as T;
}

async function requestForm<T>(
  path: string,
  formData: FormData,
  method = 'POST',
): Promise<T> {
  const headers = new Headers();
  const csrf = getCsrfToken();
  if (csrf) {
    headers.set('X-CSRFToken', csrf);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: 'include',
    headers,
    body: formData,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = formatApiError(data) || `Ошибка запроса (${response.status})`;
    throw new ApiClientError(message, response.status, data);
  }

  return data as T;
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<User>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    logout: () =>
      request<{ detail: string }>('/auth/logout', { method: 'POST' }),
    me: () => request<User>('/me'),
  },

  profile: {
    me: () => request<StudentProfile>('/profile/me'),
    update: (data: ProfileUpdatePayload | FormData) => {
      if (data instanceof FormData) {
        return requestForm<StudentProfile>('/profile/me', data, 'PATCH');
      }
      return request<StudentProfile>('/profile/me', {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
    },
  },

  students: {
    profile: (userId: number) => request<StudentProfile>(`/students/${userId}/profile`),
    submissions: {
      list: (userId: number, params?: { task_id?: number }) => {
        const search = new URLSearchParams();
        if (params?.task_id) search.set('task_id', String(params.task_id));
        const qs = search.toString();
        return request<AdminSubmission[]>(
          `/students/${userId}/submissions${qs ? `?${qs}` : ''}`,
        );
      },
    },
  },

  courses: {
    list: () => request<Course[]>('/courses'),
    get: (id: number) => request<Course>(`/courses/${id}`),
    lessons: (id: number) => request<Lesson[]>(`/courses/${id}/lessons`),
  },

  lessons: {
    get: (id: number) => request<Lesson>(`/lessons/${id}`),
    tasks: (id: number) => request<Task[]>(`/lessons/${id}/tasks`),
  },

  code: {
    run: (payload: {
      lesson_id?: number;
      task_id?: number;
      language: string;
      source_code: string;
      stdin?: string;
      repl_mode?: boolean;
    }) =>
      request<CodeRunResult>('/code/run', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  submissions: {
    create: (task_id: number, source_code: string) =>
      request<SubmissionResult>('/submissions', {
        method: 'POST',
        body: JSON.stringify({ task_id, source_code }),
      }),
    get: (id: number) => request<AdminSubmissionDetail>(`/submissions/${id}`),
    mine: () => request<AdminSubmission[]>('/submissions/me'),
  },

  badges: {
    me: () => request<UserBadge[]>('/badges/me'),
  },

  progress: {
    me: () => request<UserProgress[]>('/progress/me'),
  },

  parent: {
    children: {
      list: () => request<ChildUser[]>('/parent/children'),
      create: (data: { username: string; password: string; display_name?: string; email?: string }) =>
        request<ChildUser>('/parent/children', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      setPassword: (childId: number, password: string) =>
        request<{ detail: string }>(`/parent/children/${childId}/password`, {
          method: 'PATCH',
          body: JSON.stringify({ password }),
        }),
      progress: (childId: number) =>
        request<UserProgress[]>(`/parent/children/${childId}/progress`),
      badges: (childId: number) =>
        request<UserBadge[]>(`/parent/children/${childId}/badges`),
      submissions: {
        list: (childId: number) =>
          request<AdminSubmission[]>(`/parent/children/${childId}/submissions`),
        get: (childId: number, submissionId: number) =>
          request<AdminSubmissionDetail>(
            `/parent/children/${childId}/submissions/${submissionId}`,
          ),
      },
    },
  },

  leaderboard: {
    list: (params?: { course_id?: number; group_id?: number }) => {
      const search = new URLSearchParams();
      if (params?.course_id) search.set('course_id', String(params.course_id));
      if (params?.group_id) search.set('group_id', String(params.group_id));
      const qs = search.toString();
      return request<LeaderboardEntry[]>(`/leaderboard${qs ? `?${qs}` : ''}`);
    },
  },

  languages: {
    list: () => request<ProgrammingLanguage[]>('/languages'),
  },

  staff: {
    parents: {
      list: () => request<StaffParent[]>('/staff/parents'),
      setChildren: (parentId: number, childIds: number[]) =>
        request<StaffParent>(`/staff/parents/${parentId}/children`, {
          method: 'PATCH',
          body: JSON.stringify({ child_ids: childIds }),
        }),
    },
    students: {
      list: () => request<ChildUser[]>('/staff/students'),
    },
  },

  admin: {
    users: {
      list: (role?: string) =>
        request<User[]>(`/admin/users${role ? `?role=${role}` : ''}`),
      create: (data: Partial<User> & { password: string }) =>
        request<User>('/admin/users', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      update: (id: number, data: Partial<User> & { password?: string; child_ids?: number[] }) =>
        request<User>(`/admin/users/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      delete: (id: number) =>
        request<void>(`/admin/users/${id}`, { method: 'DELETE' }),
      resetStatistics: (id: number, data?: { include_submissions?: boolean }) =>
        request<{ detail: string }>(`/admin/users/${id}/reset-statistics`, {
          method: 'POST',
          body: JSON.stringify(data ?? {}),
        }),
      badges: {
        list: (userId: number) => request<UserBadge[]>(`/admin/users/${userId}/badges`),
        award: (userId: number, badgeId: number) =>
          request<UserBadge>(`/admin/users/${userId}/badges`, {
            method: 'POST',
            body: JSON.stringify({ badge_id: badgeId }),
          }),
        revoke: (userId: number, badgeId: number) =>
          request<void>(`/admin/users/${userId}/badges/${badgeId}`, { method: 'DELETE' }),
      },
    },
    groups: {
      list: () => request<Group[]>('/admin/groups'),
      create: (data: {
        title: string;
        description?: string;
        teacher_id?: number | null;
        member_ids?: number[];
        is_active?: boolean;
      }) =>
        request<Group>('/admin/groups', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      update: (
        id: number,
        data: {
          title?: string;
          description?: string;
          teacher_id?: number | null;
          member_ids?: number[];
          is_active?: boolean;
        },
      ) =>
        request<Group>(`/admin/groups/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      delete: (id: number) =>
        request<void>(`/admin/groups/${id}`, { method: 'DELETE' }),
    },
    courses: {
      list: () => request<Course[]>('/admin/courses'),
      get: (id: number) => request<Course>(`/admin/courses/${id}`),
      create: (data: Record<string, unknown>) =>
        request<Course>('/admin/courses', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      update: (id: number, data: Record<string, unknown>) =>
        request<Course>(`/admin/courses/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      delete: (id: number) =>
        request<void>(`/admin/courses/${id}`, { method: 'DELETE' }),
    },
    submissions: {
      list: (params?: {
        status?: string;
        course_id?: number;
        lesson_id?: number;
        user_id?: number;
        task_id?: number;
      }) => {
        const search = new URLSearchParams();
        if (params?.status) search.set('status', params.status);
        if (params?.course_id) search.set('course_id', String(params.course_id));
        if (params?.lesson_id) search.set('lesson_id', String(params.lesson_id));
        if (params?.user_id) search.set('user_id', String(params.user_id));
        if (params?.task_id) search.set('task_id', String(params.task_id));
        const qs = search.toString();
        return request<AdminSubmission[]>(`/admin/submissions${qs ? `?${qs}` : ''}`);
      },
      get: (id: number) => request<AdminSubmissionDetail>(`/admin/submissions/${id}`),
      review: (
        id: number,
        data: { status: 'accepted' | 'rejected'; teacher_comment?: string },
      ) =>
        request<AdminSubmissionDetail>(`/admin/submissions/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      recheck: (id: number) =>
        request<{ id: number; status: string; message: string }>(
          `/admin/submissions/${id}/recheck`,
          { method: 'POST' },
        ),
    },
    badges: {
      list: () => request<Badge[]>('/admin/badges'),
      create: (formData: FormData) =>
        requestForm<Badge>('/admin/badges', formData, 'POST'),
      update: (id: number, formData: FormData) =>
        requestForm<Badge>(`/admin/badges/${id}`, formData, 'PATCH'),
      delete: (id: number) =>
        request<void>(`/admin/badges/${id}`, { method: 'DELETE' }),
    },
    lessons: {
      list: (courseId?: number) =>
        request<Lesson[]>(`/admin/lessons${courseId ? `?course_id=${courseId}` : ''}`),
      get: (id: number) => request<Lesson>(`/admin/lessons/${id}`),
      create: (data: Record<string, unknown>) =>
        request<Lesson>('/admin/lessons', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      update: (id: number, data: Record<string, unknown>) =>
        request<Lesson>(`/admin/lessons/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      delete: (id: number) =>
        request<void>(`/admin/lessons/${id}`, { method: 'DELETE' }),
    },
    tasks: {
      list: (lessonId?: number) =>
        request<AdminTask[]>(`/admin/tasks${lessonId ? `?lesson_id=${lessonId}` : ''}`),
      get: (id: number) => request<AdminTask>(`/admin/tasks/${id}`),
      create: (data: Record<string, unknown>) =>
        request<AdminTask>('/admin/tasks', {
          method: 'POST',
          body: JSON.stringify(data),
        }),
      update: (id: number, data: Record<string, unknown>) =>
        request<AdminTask>(`/admin/tasks/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      delete: (id: number) =>
        request<void>(`/admin/tasks/${id}`, { method: 'DELETE' }),
    },
    import: {
      course: (file: File) => {
        const form = new FormData();
        form.append('file', file);
        return requestForm<ImportJob>('/admin/import/course', form);
      },
      lesson: (file: File, courseId: number) => {
        const form = new FormData();
        form.append('file', file);
        form.append('course_id', String(courseId));
        return requestForm<ImportJob>('/admin/import/lesson', form);
      },
      tasks: (file: File, lessonId: number) => {
        const form = new FormData();
        form.append('file', file);
        form.append('lesson_id', String(lessonId));
        return requestForm<ImportJob>('/admin/import/tasks', form);
      },
      jobs: () => request<ImportJob[]>('/admin/import/jobs'),
    },
    export: {
      course: async (courseId: number) => {
        const csrf = getCsrfToken();
        const headers = new Headers();
        if (csrf) headers.set('X-CSRFToken', csrf);
        const response = await fetch(`${API_BASE}/admin/export/course/${courseId}`, {
          credentials: 'include',
          headers,
        });
        if (!response.ok) {
          throw new ApiClientError('Ошибка экспорта', response.status, null);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `course_${courseId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      },
    },
    telegram: {
      status: () => request<TelegramStatus>('/telegram/me'),
      createLinkCode: () =>
        request<TelegramLinkCode>('/telegram/link-code', { method: 'POST' }),
      updateSettings: (data: { notify_manual_review?: boolean; notify_new_submissions?: boolean }) =>
        request<TelegramStatus>('/telegram/me', {
          method: 'PATCH',
          body: JSON.stringify(data),
        }),
      unlink: () => request<{ detail: string }>('/telegram/me', { method: 'DELETE' }),
      getBotSettings: () => request<TelegramBotSettings>('/telegram/settings'),
      updateBotSettings: (data: TelegramBotSettingsUpdate) =>
        request<TelegramBotSettings>('/telegram/settings', {
          method: 'PUT',
          body: JSON.stringify(data),
        }),
    },
  },
};

export function isStaffRole(role: string): boolean {
  return role === 'superadmin' || role === 'admin' || role === 'teacher';
}

export function isSuperAdmin(role: string): boolean {
  return role === 'superadmin';
}

export function isPlatformAdmin(role: string): boolean {
  return role === 'superadmin' || role === 'admin';
}

export function isParentRole(role: string): boolean {
  return role === 'parent';
}

export function monacoLanguage(slug: string): string {
  const map: Record<string, string> = {
    python: 'python',
    javascript: 'javascript',
    java: 'java',
    typescript: 'typescript',
  };
  return map[slug] ?? slug;
}
