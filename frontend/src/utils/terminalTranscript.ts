export interface InputStep {
  index: number;
  variable?: string;
  prompt?: string;
}

export function parseInputSteps(code: string): InputStep[] {
  const steps: InputStep[] = [];
  const pattern = /(?:(\w+)\s*=\s*)?input\s*\(\s*(?:f?(["'])(.*?)\2\s*)?\)/g;
  let match: RegExpExecArray | null;
  let index = 0;
  while ((match = pattern.exec(code)) !== null) {
    steps.push({
      index,
      variable: match[1] || undefined,
      prompt: match[3] || undefined,
    });
    index += 1;
  }
  return steps;
}

export function stdoutDelta(previous: string, next: string): string {
  if (next.startsWith(previous)) {
    return next.slice(previous.length);
  }
  return next;
}

export function buildAccumulatedStdin(lines: string[]): string {
  if (lines.length === 0) return '';
  return `${lines.join('\n')}\n`;
}
