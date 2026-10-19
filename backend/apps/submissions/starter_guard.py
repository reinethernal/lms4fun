"""Reject submissions that are unchanged relative to the task starter code."""
from __future__ import annotations

import re

from apps.tasks.demo import is_run_only_task
from apps.tasks.personalize import personalize_text


_COMMENT_RE = re.compile(r'#.*?$', re.MULTILINE)
_SPACE_AROUND_OPS = re.compile(r'\s*([=+\-*/%<>!,])\s*')


def normalize_student_code(code: str) -> str:
    """Normalize code for starter comparison: comments, blanks, spacing around ops."""
    text = (code or '').replace('\r\n', '\n').replace('\r', '\n')
    text = _COMMENT_RE.sub('', text)
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Collapse whitespace outside of simple quoted segments: split by quotes
        parts = re.split(r'(["\'].*?["\'])', line)
        rebuilt = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                rebuilt.append(part)
            else:
                part = _SPACE_AROUND_OPS.sub(r'\1', part)
                part = re.sub(r'\s+', ' ', part)
                rebuilt.append(part)
        lines.append(''.join(rebuilt).strip())
    return '\n'.join(lines)


def is_unchanged_starter(submitted: str, starter: str, user=None) -> bool:
    """True when submitted code matches personalized starter after normalization."""
    personalized = personalize_text(starter or '', user) if user is not None else (starter or '')
    candidates = {personalized, starter or ''}
    submitted_norm = normalize_student_code(submitted)
    if not submitted_norm:
        return True
    return any(submitted_norm == normalize_student_code(c) for c in candidates)


def should_reject_unchanged_starter(task, submitted: str, user=None) -> bool:
    """Whether to block this submission as an unchanged starter."""
    if is_run_only_task(task):
        return False
    return is_unchanged_starter(submitted, getattr(task, 'starter_code', '') or '', user)
