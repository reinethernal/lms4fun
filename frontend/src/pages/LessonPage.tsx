import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, ApiClientError, isParentRole } from '@/api/client';
import type { CodeRunResult, Course, Lesson, ProgrammingLanguage, Task, AdminSubmissionDetail } from '@/api/types';
import { CodeEditor } from '@/components/CodeEditor';
import { Loading } from '@/components/Loading';
import {
  SubmissionResultPanel,
  submissionBannerClass,
  submissionBannerMessage,
} from '@/components/SubmissionResultPanel';
import { Terminal } from '@/components/Terminal';
import {
  canRunPractice,
  canSubmitPractice,
  PracticeSteps,
} from '@/components/PracticeSteps';
import { isRunOnlyTask } from '@/utils/taskKind';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { statusBadgeClass, statusLabelRu, pollDataFromSubmission, countInputCalls } from '@/utils/submissionStatus';
import { isErrorGuidance, parseErrorGuidance } from '@/utils/errorGuidance';
import {
  applyRunResult,
  appendInputEcho,
  beginRun,
  createReplSession,
  type ReplSession,
} from '@/utils/replSession';
import { buildAccumulatedStdin } from '@/utils/terminalTranscript';

export function LessonPage() {
  const { user } = useAuth();
  const { showBadgeToasts } = useToast();
  const readOnly = user ? isParentRole(user.role) : false;
  const { id } = useParams<{ id: string }>();
  const lessonId = Number(id);

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [languages, setLanguages] = useState<ProgrammingLanguage[]>([]);
  const [activeTaskIndex, setActiveTaskIndex] = useState(0);
  const [code, setCode] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [output, setOutput] = useState<CodeRunResult | null>(null);
  const [replSession, setReplSession] = useState<ReplSession>(() => createReplSession());
  const [submitMessage, setSubmitMessage] = useState('');
  const [submitStatus, setSubmitStatus] = useState('');
  const [submissionResult, setSubmissionResult] = useState<AdminSubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [lessonLocked, setLessonLocked] = useState(false);
  const [lockedCourseId, setLockedCourseId] = useState<number | null>(null);
  const [taskViewed, setTaskViewed] = useState(false);
  const [hasTrialRun, setHasTrialRun] = useState(false);
  const [trialRunSuccess, setTrialRunSuccess] = useState(false);

  const activeTask = tasks[activeTaskIndex] ?? null;
  const codeChanged = activeTask ? code !== (activeTask.starter_code || '') : false;
  const submitAccepted = submitStatus === 'accepted';
  const submitSubmitted = submitAccepted || submitStatus === 'manual_review';
  const errorHighlightLine = useMemo(() => {
    if (!submissionResult?.checker_result) return null;
    const guidance = submissionResult.checker_result.error_guidance;
    if (isErrorGuidance(guidance) && guidance.line != null) {
      return guidance.line;
    }
    return null;
  }, [submissionResult]);
  const runOnlyTask = activeTask ? isRunOnlyTask(activeTask.title) : false;
  const practiceProps = {
    codeChanged,
    taskViewed,
    hasTrialRun,
    trialRunSuccess,
    submitAccepted,
    submitSubmitted,
    runOnlyTask,
  };
  const canRun = canRunPractice(practiceProps);
  const canSubmit = canSubmitPractice(practiceProps);
  const inputCount = countInputCalls(code);
  const allowedLanguages = useMemo(() => {
    if (course?.primary_language) {
      return [course.primary_language];
    }
    const ids = new Set<number>();
    if (lesson?.language) ids.add(lesson.language);
    tasks.forEach((t) => {
      if (t.language) ids.add(t.language);
    });
    return languages.filter((l) => ids.has(l.id));
  }, [course, lesson, tasks, languages]);

  const effectiveLanguage = useMemo((): ProgrammingLanguage | null => {
    if (course?.primary_language) {
      return course.primary_language;
    }
    const taskLang = activeTask?.language
      ? languages.find((l) => l.id === activeTask.language)
      : null;
    if (taskLang) return taskLang;
    const lessonLang = lesson?.language
      ? languages.find((l) => l.id === lesson.language)
      : null;
    if (lessonLang) return lessonLang;
    return allowedLanguages[0] ?? null;
  }, [course, lesson, activeTask, languages, allowedLanguages]);

  const currentLang = effectiveLanguage?.slug ?? selectedLanguage;
  const showLanguageSelect =
    !course?.primary_language && allowedLanguages.length > 1;

  useEffect(() => {
    if (!lessonId) return;
    void (async () => {
      setLessonLocked(false);
      setLockedCourseId(null);
      setError('');
      try {
        const [lessonData, tasksData, langs] = await Promise.all([
          api.lessons.get(lessonId),
          api.lessons.tasks(lessonId),
          api.languages.list(),
        ]);
        const courseData = await api.courses.get(lessonData.course);
        setLesson(lessonData);
        setCourse(courseData);
        const sorted = tasksData.sort((a, b) => a.sort_order - b.sort_order);
        setTasks(sorted);
        setLanguages(langs);
        if (sorted.length > 0) {
          setCode(sorted[0].starter_code || '');
        }
        const courseLangSlug = courseData.primary_language?.slug;
        const lessonLangSlug = langs.find((l) => l.id === lessonData.language)?.slug;
        const taskLangSlug = sorted[0]?.language
          ? langs.find((l) => l.id === sorted[0].language)?.slug
          : null;
        setSelectedLanguage(
          courseLangSlug ?? taskLangSlug ?? lessonLangSlug ?? langs[0]?.slug ?? 'python',
        );
      } catch (err) {
        if (
          err instanceof ApiClientError
          && typeof err.data === 'object'
          && err.data !== null
          && 'is_locked' in err.data
        ) {
          setLessonLocked(true);
          const payload = err.data as { course_id?: number };
          setLockedCourseId(payload.course_id ?? null);
        } else {
          setError('Не удалось загрузить урок');
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [lessonId]);

  useEffect(() => {
    if (!activeTask) return;
    setTaskViewed(false);
    setHasTrialRun(false);
    setTrialRunSuccess(false);
    setCode(activeTask.starter_code || '');
    setReplSession(createReplSession());
    setOutput(null);
    setSubmitMessage('');
    setSubmitStatus('');
    setSubmissionResult(null);
    if (course?.primary_language) {
      setSelectedLanguage(course.primary_language.slug);
      return;
    }
    const taskLang = activeTask.language
      ? languages.find((l) => l.id === activeTask.language)?.slug
      : null;
    const lessonLang = lesson?.language
      ? languages.find((l) => l.id === lesson.language)?.slug
      : null;
    if (taskLang) setSelectedLanguage(taskLang);
    else if (lessonLang) setSelectedLanguage(lessonLang);
  }, [activeTask, lesson, languages, course]);

  function handleCodeChange(nextCode: string) {
    setCode(nextCode);
    if (replSession.phase !== 'idle') {
      setReplSession(createReplSession());
      setOutput(null);
      setHasTrialRun(false);
      setTrialRunSuccess(false);
    }
  }

  async function handleRun() {
    if (!activeTask || !canRun) return;
    setRunning(true);
    setOutput(null);
    setSubmitMessage('');
    setError('');

    const isRepl = inputCount > 0;
    const freshSession = beginRun(createReplSession());
    setReplSession(freshSession);

    try {
      const result = await api.code.run({
        lesson_id: lessonId,
        task_id: activeTask.id,
        language: currentLang,
        source_code: code,
        stdin: '',
        repl_mode: isRepl,
      });
      setHasTrialRun(true);
      setTrialRunSuccess(result.status === 'success');
      setOutput(result);
      setReplSession(applyRunResult(freshSession, result, code));
      if (result.new_badges?.length) {
        showBadgeToasts(result.new_badges);
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        const guidance = parseErrorGuidance(err.data);
        if (guidance) {
          setHasTrialRun(true);
          setTrialRunSuccess(false);
          const errorResult: CodeRunResult = {
            status: 'error',
            language: currentLang,
            stdout: '',
            stderr: guidance.raw ?? '',
            compile_output: '',
            execution_time: null,
            memory_used: null,
            error_guidance: guidance,
          };
          setOutput(errorResult);
          setReplSession(applyRunResult(freshSession, errorResult, code));
          setError('');
          return;
        }
      }
      setError(err instanceof Error ? err.message : 'Ошибка запуска');
    } finally {
      setRunning(false);
    }
  }

  async function handleReplSubmit(line: string) {
    if (!activeTask || running || replSession.phase !== 'waiting_input') return;
    setRunning(true);
    setError('');

    const withEcho = appendInputEcho(replSession, line);
    setReplSession(withEcho);

    try {
      const result = await api.code.run({
        lesson_id: lessonId,
        task_id: activeTask.id,
        language: currentLang,
        source_code: code,
        stdin: buildAccumulatedStdin(withEcho.stdinLines),
        repl_mode: true,
      });
      setHasTrialRun(true);
      setTrialRunSuccess(result.status === 'success');
      setOutput(result);
      setReplSession(applyRunResult(withEcho, result, code));
      if (result.new_badges?.length) {
        showBadgeToasts(result.new_badges);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка запуска');
    } finally {
      setRunning(false);
    }
  }

  async function pollSubmission(submissionId: number) {
    const maxAttempts = 20;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      const detail = await api.submissions.get(submissionId);
      setSubmitStatus(detail.status);
      if (detail.status !== 'pending') {
        setSubmissionResult(detail);
        setSubmitMessage(submissionBannerMessage(detail));
        const result = pollDataFromSubmission(detail);
        if (result.new_badges?.length) {
          showBadgeToasts(result.new_badges);
        }
        if (result.stdout || result.stderr || result.compile_output || result.error_guidance) {
          setOutput({
            status: result.status,
            language: currentLang,
            stdout: result.stdout ?? '',
            stderr: result.stderr ?? '',
            compile_output: result.compile_output ?? '',
            execution_time: null,
            memory_used: null,
            error_guidance: result.error_guidance,
          });
          if (result.error_guidance) {
            setReplSession((session) => ({
              ...session,
              phase: 'error',
              lines: [
                ...session.lines,
                { type: 'error' as const, guidance: result.error_guidance! },
              ],
            }));
          }
        }
        return;
      }
    }
    setSubmitMessage('Проверка занимает больше времени, чем ожидалось.');
  }

  async function handleSubmit() {
    if (!activeTask || !canSubmit) return;
    setSubmitting(true);
    setSubmitMessage('');
    setSubmitStatus('pending');
    setSubmissionResult(null);
    setError('');
    try {
      const result = await api.submissions.create(activeTask.id, code);
      setSubmitStatus(result.status);
      setSubmitMessage(result.message);
      if (result.id && result.status === 'pending') {
        await pollSubmission(result.id);
      } else if (result.xp_awarded) {
        setSubmitMessage(`${result.message} (+${result.xp_awarded} XP)`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки');
    } finally {
      setSubmitting(false);
    }
  }

  function handleResetCode() {
    if (!activeTask) return;
    setCode(activeTask.starter_code || '');
    setOutput(null);
    setReplSession(createReplSession());
    setHasTrialRun(false);
    setTrialRunSuccess(false);
    setSubmitMessage('');
    setSubmitStatus('');
    setSubmissionResult(null);
  }

  function handleClearOutput() {
    setOutput(null);
    setReplSession(createReplSession());
    setHasTrialRun(false);
    setTrialRunSuccess(false);
  }

  if (loading) return <Loading />;

  if (lessonLocked) {
    return (
      <div>
        <h1 className="page-title">Урок закрыт</h1>
        <div className="card">
          <p>Сначала пройдите предыдущий урок — сдайте все обязательные задания.</p>
          {lockedCourseId && (
            <Link to={`/courses/${lockedCourseId}`} className="btn btn-primary mt-md">
              Вернуться к курсу
            </Link>
          )}
        </div>
      </div>
    );
  }

  if (error && !lesson) return <div className="error-banner">{error}</div>;
  if (!lesson) return <div className="error-banner">Урок не найден</div>;

  return (
    <div>
      <p>
        <Link to={`/courses/${lesson.course}`}>← Назад к курсу</Link>
      </p>
      <h1 className="page-title">
        Урок {lesson.number}: {lesson.title}
      </h1>

      {error && <div className="error-banner">{error}</div>}

      {readOnly && (
        <div className="info-banner mb-md">
          Режим наблюдения: вы можете читать урок, но не запускать и не сдавать код.
        </div>
      )}

      <div className="lesson-layout">
        <section className="card theory-panel markdown-body">
          <h2>Теория</h2>
          {lesson.theory_text ? (
            <div className="pre-wrap">{lesson.theory_text}</div>
          ) : (
            <p className="text-muted">Теория не добавлена.</p>
          )}
          {lesson.simple_explanation && (
            <>
              <h3>Простыми словами</h3>
              <div className="pre-wrap">{lesson.simple_explanation}</div>
            </>
          )}
          {lesson.practice_text && (
            <>
              <h3>Практика</h3>
              <div className="pre-wrap">{lesson.practice_text}</div>
            </>
          )}
          {lesson.mini_project_text && (
            <>
              <h3>Мини-проект</h3>
              <div className="pre-wrap">{lesson.mini_project_text}</div>
            </>
          )}
          {lesson.summary_text && (
            <>
              <h3>Итог урока</h3>
              <div className="pre-wrap">{lesson.summary_text}</div>
            </>
          )}
        </section>

        <section className="editor-panel">
          {tasks.length > 1 && (
            <div className="task-tabs" role="tablist" aria-label="Задания урока">
              {tasks.map((t, i) => (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={i === activeTaskIndex}
                  className={`task-tab${i === activeTaskIndex ? ' task-tab-active' : ''}`}
                  onClick={() => setActiveTaskIndex(i)}
                >
                  <span className="task-tab-num">{i + 1}</span>
                  {t.title}
                </button>
              ))}
            </div>
          )}

          {activeTask && (
            <div className="card task-goal-card">
              {tasks.length === 1 && <h3 className="task-goal-title">{activeTask.title}</h3>}
              <p className="task-goal-description">{activeTask.description}</p>
              {runOnlyTask ? (
                <span className="badge task-goal-badge-demo">Пример — без оценки</span>
              ) : (
                <span className="badge badge-xp">Можно получить {activeTask.max_xp} XP</span>
              )}
              {!readOnly && !taskViewed && (
                <div className="mt-md">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setTaskViewed(true)}
                  >
                    Я прочитал задание
                  </button>
                </div>
              )}
            </div>
          )}

          {!readOnly && (
            <PracticeSteps {...practiceProps} />
          )}

          {!readOnly && showLanguageSelect && (
            <div className="form-group">
              <label>Язык программирования</label>
              <select
                value={currentLang}
                onChange={(e) => setSelectedLanguage(e.target.value)}
              >
                {allowedLanguages.map((l) => (
                  <option key={l.id} value={l.slug}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {!readOnly && !showLanguageSelect && effectiveLanguage && (
            <p className="text-muted text-sm">Язык: {effectiveLanguage.name}</p>
          )}

          <div className="editor-label-block">
            <label className="editor-section-label">
              {readOnly || runOnlyTask ? 'Пример кода' : 'Твой код'}
            </label>
            {!readOnly && !runOnlyTask && (
              <p className="hint-text">Меняй программу прямо здесь</p>
            )}
          </div>

          {readOnly || runOnlyTask ? (
            <pre className="code-block">{activeTask?.starter_code || code || '—'}</pre>
          ) : (
            <CodeEditor
              value={code}
              language={currentLang}
              onChange={handleCodeChange}
              highlightLine={errorHighlightLine}
            />
          )}

          {!readOnly && (
            <div className="editor-toolbar">
              <div className="editor-toolbar-primary">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => void handleRun()}
                  disabled={running || !activeTask || !canRun}
                  title={!canRun ? 'Сначала прочитайте задание' : undefined}
                >
                  {running
                    ? runOnlyTask
                      ? 'Запуск…'
                      : 'Проверка…'
                    : runOnlyTask
                      ? 'Запустить'
                      : 'Проверить программу'}
                </button>
                {!runOnlyTask && (
                  <>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => void handleSubmit()}
                      disabled={submitting || !activeTask || !canSubmit}
                      title={!canSubmit ? 'Сначала успешно проверьте программу' : undefined}
                    >
                      {submitting ? 'Отправка…' : 'Сдать задание'}
                    </button>
                    {submitStatus && (
                      <span className={`badge ${statusBadgeClass(submitStatus)}`}>
                        {statusLabelRu(submitStatus)}
                      </span>
                    )}
                  </>
                )}
              </div>
              {!runOnlyTask && (
                <div className="editor-toolbar-secondary">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleResetCode}
                    disabled={!activeTask}
                  >
                    Сбросить код
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleClearOutput}
                    disabled={!output}
                  >
                    Очистить результат
                  </button>
                </div>
              )}
            </div>
          )}

          {!readOnly && !runOnlyTask && (
            <div className="toolbar-hints">
              <p className="hint-text">
                <strong>Проверить программу</strong> — запусти код и посмотри результат (XP не начисляется).
              </p>
              <p className="hint-text">
                <strong>Сдать задание</strong> — отправь на автопроверку и получи XP.
              </p>
            </div>
          )}

          {!readOnly && runOnlyTask && (
            <div className="toolbar-hints">
              <p className="hint-text">
                <strong>Запустить</strong> — посмотри, как работает пример. Код менять не нужно.
              </p>
            </div>
          )}

          {!readOnly && !runOnlyTask && submitMessage && (
            <div className={submissionBannerClass(submitStatus)}>
              {submitMessage}
            </div>
          )}

          {!readOnly && !runOnlyTask && submissionResult && (
            <SubmissionResultPanel submission={submissionResult} />
          )}

          {!readOnly && (
            <Terminal
              session={replSession}
              lastResult={output}
              running={running}
              inputCount={inputCount}
              hasStarted={hasTrialRun}
              sourceCode={code}
              isDemo={runOnlyTask}
              onReplSubmit={handleReplSubmit}
            />
          )}
        </section>
      </div>
    </div>
  );
}
