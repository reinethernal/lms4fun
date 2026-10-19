export function isRunOnlyTask(title: string): boolean {
  return title.trim().toLowerCase().startsWith('запусти');
}
