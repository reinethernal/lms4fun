def is_run_only_task(task) -> bool:
    """Demo task: title starts with «Запусти» — run-only, no submission required."""
    return (getattr(task, 'title', None) or '').strip().lower().startswith('запусти')
