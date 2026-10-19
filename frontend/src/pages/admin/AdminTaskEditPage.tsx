import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import type { AdminTask, Lesson, ProgrammingLanguage, TaskTestCase } from '@/api/types';
import { TaskTestsEditor } from '@/components/TaskTestsEditor';
import { Loading } from '@/components/Loading';

const CHECKER_TYPES = [
  { value: 'stdout_exact', label: 'Точное совпадение stdout' },
  { value: 'stdout_regex', label: 'Регулярное выражение stdout' },
  { value: 'stdin_stdout', label: 'Тесты stdin/stdout' },
  { value: 'custom', label: 'Пользовательская проверка' },
  { value: 'manual', label: 'Ручная проверка' },
];

function normalizeTests(value: unknown): TaskTestCase[] {
  if (!Array.isArray(value)) return [];
  return value.map((t) => {
    if (typeof t !== 'object' || t === null) return { stdin: '', expected_stdout: '' };
    const row = t as TaskTestCase;
    return {
      stdin: row.stdin ?? '',
      expected_stdout: row.expected_stdout ?? '',
      pattern: row.pattern,
      hidden: row.hidden,
    };
  });
}

const emptyForm = (lessonId: number, languageId: number, sortOrder: number) => ({
  lesson: lessonId,
  language: languageId,
  slug: '',
  title: '',
  description: '',
  task_type: 'practice',
  starter_code: '',
  solution_template: '',
  stdin: '',
  expected_stdout: '',
  expected_stderr: '',
  checker_type: 'stdout_exact',
  checker_code: '',
  visible_tests_json: [] as TaskTestCase[],
  hidden_tests_json: [] as TaskTestCase[],
  checker_config_json: {} as Record<string, unknown>,
  max_xp: 10,
  difficulty: 'easy',
  is_required: true,
  sort_order: sortOrder,
});

export function AdminTaskEditPage() {
  const { lessonId, taskId } = useParams<{ lessonId: string; taskId: string }>();
  const lessonIdNum = Number(lessonId);
  const isNew = taskId === 'new';
  const taskIdNum = isNew ? null : Number(taskId);
  const navigate = useNavigate();

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [languages, setLanguages] = useState<ProgrammingLanguage[]>([]);
  const [form, setForm] = useState<ReturnType<typeof emptyForm> | null>(null);
  const [regexPattern, setRegexPattern] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!lessonIdNum) return;
    void (async () => {
      try {
        const [lessonData, langs, tasks] = await Promise.all([
          api.admin.lessons.get(lessonIdNum),
          api.languages.list(),
          api.admin.tasks.list(lessonIdNum),
        ]);
        setLesson(lessonData);
        setLanguages(langs);
        const defaultLang = lessonData.language ?? langs[0]?.id ?? 0;

        if (isNew) {
          setForm(emptyForm(lessonIdNum, defaultLang, tasks.length));
        } else if (taskIdNum) {
          const task: AdminTask = await api.admin.tasks.get(taskIdNum);
          setForm({
            lesson: task.lesson,
            language: task.language,
            slug: task.slug || '',
            title: task.title,
            description: task.description || '',
            task_type: task.task_type || 'practice',
            starter_code: task.starter_code || '',
            solution_template: task.solution_template || '',
            stdin: task.stdin || '',
            expected_stdout: task.expected_stdout || '',
            expected_stderr: task.expected_stderr || '',
            checker_type: task.checker_type || 'stdout_exact',
            checker_code: task.checker_code || '',
            visible_tests_json: normalizeTests(task.visible_tests_json),
            hidden_tests_json: normalizeTests(task.hidden_tests_json),
            checker_config_json: task.checker_config_json || {},
            max_xp: task.max_xp,
            difficulty: task.difficulty || 'easy',
            is_required: task.is_required,
            sort_order: task.sort_order,
          });
          const config = task.checker_config_json || {};
          setRegexPattern(typeof config.pattern === 'string' ? config.pattern : '');
        }
      } catch {
        setError('Не удалось загрузить задание');
      } finally {
        setLoading(false);
      }
    })();
  }, [lessonIdNum, taskIdNum, isNew]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError('');
    setSuccess('');

    const payload: Record<string, unknown> = {
      ...form,
      checker_config_json:
        form.checker_type === 'stdout_regex'
          ? { pattern: regexPattern }
          : form.checker_config_json,
    };

    try {
      if (isNew) {
        const created = await api.admin.tasks.create(payload);
        setSuccess('Задание создано');
        navigate(`/admin/lessons/${lessonIdNum}/tasks/${created.id}/edit`, { replace: true });
      } else if (taskIdNum) {
        await api.admin.tasks.update(taskIdNum, payload);
        setSuccess('Задание сохранено');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения');
    }
  }

  if (loading) return <Loading />;
  if (!lesson || !form) return <div className="error-banner">Задание не найдено</div>;

  return (
    <div>
      <p>
        <Link to={`/admin/lessons/${lessonIdNum}/edit`}>← {lesson.title}</Link>
      </p>
      <h1 className="page-title">{isNew ? 'Новое задание' : `Редактирование: ${form.title}`}</h1>
      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="card mt-md">
        <h2>Основное</h2>
        <div className="form-row-grid">
          <div className="form-group">
            <label>Название</label>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Slug</label>
            <input
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              placeholder="task-1"
            />
          </div>
          <div className="form-group">
            <label>Тип</label>
            <select
              value={form.task_type}
              onChange={(e) => setForm({ ...form, task_type: e.target.value })}
            >
              <option value="practice">Практика</option>
              <option value="challenge">Челлендж</option>
              <option value="project">Проект</option>
              <option value="quiz">Квиз</option>
            </select>
          </div>
          <div className="form-group">
            <label>Язык</label>
            <select
              value={form.language}
              onChange={(e) => setForm({ ...form, language: Number(e.target.value) })}
              required
            >
              {languages.map((l) => (
                <option key={l.id} value={l.id}>{l.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>XP</label>
            <input
              type="number"
              value={form.max_xp}
              onChange={(e) => setForm({ ...form, max_xp: Number(e.target.value) })}
            />
          </div>
          <div className="form-group">
            <label>Сложность</label>
            <select
              value={form.difficulty}
              onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
            >
              <option value="easy">Лёгкая</option>
              <option value="medium">Средняя</option>
              <option value="hard">Сложная</option>
            </select>
          </div>
          <div className="form-group">
            <label>Порядок</label>
            <input
              type="number"
              value={form.sort_order}
              onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
            />
          </div>
        </div>
        <div className="form-group">
          <label>Описание</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={4}
          />
        </div>
        <label>
          <input
            type="checkbox"
            checked={form.is_required}
            onChange={(e) => setForm({ ...form, is_required: e.target.checked })}
          />
          {' '}Обязательное задание
        </label>

        <h2 className="mt-lg">Код</h2>
        <div className="form-group">
          <label>Стартовый код</label>
          <textarea
            className="code-textarea"
            rows={10}
            value={form.starter_code}
            onChange={(e) => setForm({ ...form, starter_code: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Шаблон решения</label>
          <textarea
            className="code-textarea"
            rows={6}
            value={form.solution_template}
            onChange={(e) => setForm({ ...form, solution_template: e.target.value })}
          />
        </div>

        <h2 className="mt-lg">Проверка</h2>
        <div className="form-group">
          <label>Тип проверки</label>
          <select
            value={form.checker_type}
            onChange={(e) => setForm({ ...form, checker_type: e.target.value })}
          >
            {CHECKER_TYPES.map((ct) => (
              <option key={ct.value} value={ct.value}>{ct.label}</option>
            ))}
          </select>
        </div>

        {form.checker_type === 'stdout_exact' && (
          <>
            <div className="form-group">
              <label>stdin</label>
              <textarea
                className="code-textarea"
                rows={3}
                value={form.stdin}
                onChange={(e) => setForm({ ...form, stdin: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>expected_stdout</label>
              <textarea
                className="code-textarea"
                rows={3}
                value={form.expected_stdout}
                onChange={(e) => setForm({ ...form, expected_stdout: e.target.value })}
              />
            </div>
          </>
        )}

        {form.checker_type === 'stdout_regex' && (
          <div className="form-group">
            <label>Регулярное выражение (pattern)</label>
            <input
              value={regexPattern}
              onChange={(e) => setRegexPattern(e.target.value)}
              placeholder="^Hello.*"
            />
          </div>
        )}

        {form.checker_type === 'stdin_stdout' && (
          <>
            <TaskTestsEditor
              label="Видимые тесты"
              tests={form.visible_tests_json}
              onChange={(visible_tests_json) => setForm({ ...form, visible_tests_json })}
            />
            <TaskTestsEditor
              label="Скрытые тесты"
              tests={form.hidden_tests_json}
              onChange={(hidden_tests_json) => setForm({ ...form, hidden_tests_json })}
              showHidden
            />
          </>
        )}

        {form.checker_type === 'custom' && (
          <div className="form-group">
            <label>checker_code</label>
            <p className="hint-text">Пользовательская проверка в runtime может быть не реализована.</p>
            <textarea
              className="code-textarea"
              rows={8}
              value={form.checker_code}
              onChange={(e) => setForm({ ...form, checker_code: e.target.value })}
            />
          </div>
        )}

        {form.checker_type === 'manual' && (
          <p className="hint-text">
            Решения будут отправляться на ручную проверку преподавателем (статус «На проверке»).
          </p>
        )}

        <div className="modal-actions mt-lg">
          <Link to={`/admin/lessons/${lessonIdNum}/edit`} className="btn btn-secondary">
            Отмена
          </Link>
          <button type="submit" className="btn btn-primary">
            {isNew ? 'Создать' : 'Сохранить'}
          </button>
        </div>
      </form>
    </div>
  );
}
