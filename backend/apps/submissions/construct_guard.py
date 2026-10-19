"""Static checks that submitted code uses required language constructs."""
from __future__ import annotations

import re
from typing import Any


_COMMENT_RE = re.compile(r'#.*?$', re.MULTILINE)


def _code_without_comments(source_code: str) -> str:
    return _COMMENT_RE.sub('', source_code or '')


def check_required_constructs(source_code: str, config: dict[str, Any] | None) -> str | None:
    """
    Return an error message if required constructs are missing, else None.

    Config keys:
      - required_constructs: list[str] — all must appear as substrings (word-ish)
      - required_any: list[list[str]] — each group: at least one item must appear
    """
    if not config:
        return None
    text = _code_without_comments(source_code)
    text_lower = text.lower()

    missing = []
    for token in config.get('required_constructs') or []:
        if not token:
            continue
        if not _token_present(text, text_lower, token):
            missing.append(token)
    if missing:
        return (
            'В решении не хватает обязательных конструкций: '
            + ', '.join(f'`{m}`' for m in missing)
            + '. Используй то, что изучается в уроке.'
        )

    for group in config.get('required_any') or []:
        if not group:
            continue
        if not any(_token_present(text, text_lower, token) for token in group if token):
            return (
                'В решении нужна одна из конструкций: '
                + ' / '.join(f'`{t}`' for t in group)
                + '.'
            )
    return None


def _token_present(text: str, text_lower: str, token: str) -> bool:
    token = token.strip()
    if not token:
        return True
    # Prefer word-boundary match for identifiers/keywords
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', token):
        return re.search(rf'\b{re.escape(token)}\b', text, re.IGNORECASE) is not None
    return token.lower() in text_lower
