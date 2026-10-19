import { useEffect, useRef, useState } from 'react';
import { ErrorGuidance } from '@/components/ErrorGuidance';
import type { CodeRunResult } from '@/api/types';
import type { ReplSession } from '@/utils/replSession';
import { buildAccumulatedStdin, parseInputSteps } from '@/utils/terminalTranscript';
import { resolveErrorGuidance } from '@/utils/parseExecutionError';

interface TerminalProps {
  session: ReplSession;
  lastResult: CodeRunResult | null;
  running: boolean;
  inputCount: number;
  hasStarted: boolean;
  sourceCode: string;
  readOnly?: boolean;
  isDemo?: boolean;
  onReplSubmit: (line: string) => void;
}

export function Terminal({
  session,
  lastResult,
  running,
  inputCount,
  hasStarted,
  sourceCode,
  readOnly = false,
  isDemo = false,
  onReplSubmit,
}: TerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [inputLine, setInputLine] = useState('');

  const showInputLine = inputCount > 0 && session.phase === 'waiting_input' && !readOnly;
  const inputSteps = parseInputSteps(sourceCode);
  const currentStep = inputSteps[session.inputStepIndex];
  const inputPlaceholder = currentStep?.variable
    ? `Введи значение для ${currentStep.variable}`
    : 'Введи ответ и нажми Enter';

  useEffect(() => {
    if (showInputLine) {
      inputRef.current?.focus();
    }
  }, [showInputLine, session.inputStepIndex]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [session.lines, running, showInputLine]);

  const compileGuidance =
    lastResult?.compile_output || lastResult?.status === 'compile_error'
      ? resolveErrorGuidance(undefined, {
          compileOutput: lastResult?.compile_output ?? '',
          status: 'compile_error',
          sourceCode,
        })
      : undefined;

  const runtimeGuidance =
    lastResult && lastResult.status !== 'success' && lastResult.status !== 'waiting_input'
      ? resolveErrorGuidance(lastResult.error_guidance, {
          stderr: lastResult.stderr ?? '',
          status: lastResult.status,
          sourceCode,
          stdin: buildAccumulatedStdin(session.stdinLines),
        })
      : undefined;

  function handleSubmitInput() {
    const trimmed = inputLine.trimEnd();
    if (!trimmed || running) return;
    setInputLine('');
    onReplSubmit(trimmed);
  }

  return (
    <div className="terminal">
      <div className="terminal-header">
        <span>Терминал</span>
        {lastResult?.execution_time != null && lastResult.execution_time > 0 && (
          <span className="output-meta">{lastResult.execution_time.toFixed(2)} с</span>
        )}
      </div>

      <div className="terminal-scrollback" ref={scrollRef}>
        {!hasStarted ? (
          <p className="terminal-empty hint-text">
            {isDemo
              ? 'Нажми «Запустить», чтобы увидеть, как работает пример.'
              : 'Нажми «Проверить программу», чтобы запустить код здесь.'}
          </p>
        ) : (
          session.lines.map((line, index) => {
            if (line.type === 'stdout') {
              return (
                <pre key={`stdout-${index}`} className="terminal-line terminal-stdout">
                  {line.text || '—'}
                </pre>
              );
            }
            if (line.type === 'input_echo') {
              return (
                <div key={`input-${index}`} className="terminal-line terminal-input-echo">
                  <span className="terminal-prompt">&gt;</span>
                  <span>{line.text}</span>
                </div>
              );
            }
            return (
              <div key={`error-${index}`} className="terminal-line terminal-error-block">
                <ErrorGuidance guidance={line.guidance} variant="runtime" />
              </div>
            );
          })
        )}

        {running && (
          <p className="terminal-line terminal-running hint-text">Выполняется…</p>
        )}

        {showInputLine && !running && (
          <>
            {currentStep?.variable && (
              <p className="terminal-variable-hint hint-text">
                Напиши ответ — он сохранится в переменную{' '}
                <code className="terminal-variable-name">{currentStep.variable}</code>
              </p>
            )}
            <div className="terminal-line terminal-input-row">
              <span className="terminal-prompt">&gt;</span>
              <input
                ref={inputRef}
                type="text"
                className="terminal-input"
                value={inputLine}
                onChange={(e) => setInputLine(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSubmitInput();
                  }
                }}
                placeholder={inputPlaceholder}
                aria-label="Ввод для программы"
              />
            </div>
          </>
        )}
      </div>

      {compileGuidance && (
        <div className="terminal-errors">
          <ErrorGuidance guidance={compileGuidance} variant="compile" />
        </div>
      )}

      {runtimeGuidance && session.phase === 'error' && !session.lines.some((l) => l.type === 'error') && (
        <div className="terminal-errors">
          <ErrorGuidance guidance={runtimeGuidance} variant="runtime" />
        </div>
      )}

      {inputCount > 0 && hasStarted && session.phase === 'waiting_input' && !currentStep?.variable && (
        <p className="terminal-hint hint-text">
          Программа ждёт ввод — напиши ответ на строке <code>&gt;</code> и нажми Enter.
        </p>
      )}
    </div>
  );
}
