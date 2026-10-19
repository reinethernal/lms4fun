export interface ErrorGuidance {
  error_type: string;
  title: string;
  summary: string;
  attention: string[];
  why?: string;
  line?: number;
  raw?: string;
}

export function isErrorGuidance(value: unknown): value is ErrorGuidance {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.error_type === 'string'
    && typeof obj.title === 'string'
    && typeof obj.summary === 'string'
    && Array.isArray(obj.attention)
  );
}

export function parseErrorGuidance(data: unknown): ErrorGuidance | undefined {
  if (typeof data !== 'object' || data === null) return undefined;
  const guidance = (data as Record<string, unknown>).error_guidance;
  return isErrorGuidance(guidance) ? guidance : undefined;
}
