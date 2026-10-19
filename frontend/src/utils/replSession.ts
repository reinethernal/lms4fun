import type { CodeRunResult } from '@/api/types';
import type { ErrorGuidance } from '@/utils/errorGuidance';
import { parseInputSteps, stdoutDelta } from '@/utils/terminalTranscript';

export type TerminalLine =
  | { type: 'stdout'; text: string }
  | { type: 'input_echo'; text: string }
  | { type: 'error'; guidance: ErrorGuidance };

export type ReplPhase = 'idle' | 'running' | 'waiting_input' | 'done' | 'error';

export interface ReplSession {
  lines: TerminalLine[];
  stdinLines: string[];
  lastStdout: string;
  phase: ReplPhase;
  inputStepIndex: number;
}

export function createReplSession(): ReplSession {
  return {
    lines: [],
    stdinLines: [],
    lastStdout: '',
    phase: 'idle',
    inputStepIndex: 0,
  };
}

export function beginRun(session: ReplSession): ReplSession {
  return { ...session, phase: 'running' };
}

export function appendInputEcho(session: ReplSession, line: string): ReplSession {
  return {
    ...session,
    lines: [...session.lines, { type: 'input_echo', text: line }],
    stdinLines: [...session.stdinLines, line],
    phase: 'running',
  };
}

export function applyRunResult(
  session: ReplSession,
  result: CodeRunResult,
  code: string,
): ReplSession {
  const delta = stdoutDelta(session.lastStdout, result.stdout ?? '');
  const lines = [...session.lines];
  if (delta) {
    lines.push({ type: 'stdout', text: delta });
  }

  const nextStdout = result.stdout ?? '';

  if (result.status === 'waiting_input' || result.waiting_for_input) {
    const steps = parseInputSteps(code);
    return {
      ...session,
      lines,
      lastStdout: nextStdout,
      phase: 'waiting_input',
      inputStepIndex: Math.min(session.stdinLines.length, Math.max(steps.length - 1, 0)),
    };
  }

  if (result.status === 'success') {
    return {
      ...session,
      lines,
      lastStdout: nextStdout,
      phase: 'done',
    };
  }

  if (result.error_guidance) {
    lines.push({ type: 'error', guidance: result.error_guidance });
  }

  return {
    ...session,
    lines,
    lastStdout: nextStdout,
    phase: 'error',
  };
}
