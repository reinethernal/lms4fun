from __future__ import annotations

import html

from django.conf import settings

from apps.submissions.models import Submission

STATUS_LABELS = dict(Submission.Status.choices)
MAX_CODE_CHARS = 2800


def escape(text: str) -> str:
    return html.escape(text or '', quote=False)


def truncate(text: str, limit: int = MAX_CODE_CHARS) -> str:
    text = text or ''
    if len(text) <= limit:
        return text
    return text[: limit - 20] + '\n… (обрезано)'


def format_submission_card(submission: Submission, *, include_code: bool = False) -> str:
    student = submission.user.display_name or submission.user.username
    lesson = submission.task.lesson
    course = lesson.course
    status = STATUS_LABELS.get(submission.status, submission.status)
    student_profile_url = build_student_profile_url(submission.user_id)
    lines = [
        f'<b>Решение #{submission.id}</b>',
        f'Ученик: <a href="{escape(student_profile_url)}">{escape(student)}</a>',
        f'Курс: {escape(course.title)}',
        f'Урок: {escape(lesson.title)}',
        f'Задание: {escape(submission.task.title)}',
        f'Статус: <b>{escape(status)}</b>',
        f'Отправлено: {submission.submitted_at:%d.%m.%Y %H:%M}',
    ]
    if submission.teacher_comment:
        lines.append(f'Комментарий: {escape(submission.teacher_comment)}')
    if include_code:
        lines.append('')
        lines.append('<b>Код:</b>')
        lines.append(f'<pre>{escape(truncate(submission.code))}</pre>')
    return '\n'.join(lines)


def review_keyboard(submission_id: int, *, with_code: bool = False) -> dict:
    rows = [
        [
            {'text': '✅ Принять', 'callback_data': f'rv:{submission_id}:accept'},
            {'text': '❌ Отклонить', 'callback_data': f'rv:{submission_id}:reject'},
        ],
        [
            {'text': '💬 С комментарием', 'callback_data': f'rv:{submission_id}:comment'},
            {
                'text': '📄 Скрыть код' if with_code else '📄 Показать код',
                'callback_data': f'rv:{submission_id}:{"hidecode" if with_code else "code"}',
            },
        ],
        [
            {'text': '🔄 Перепроверить', 'callback_data': f'rv:{submission_id}:recheck'},
        ],
    ]
    return {'inline_keyboard': rows}


def pending_list_keyboard(items: list[tuple[int, str]]) -> dict:
    rows = [[{'text': title[:60], 'callback_data': f'rv:{sid}:open'}] for sid, title in items]
    return {'inline_keyboard': rows}


def comment_choice_keyboard(submission_id: int) -> dict:
    return {
        'inline_keyboard': [
            [
                {'text': '✅ Принять с комментарием', 'callback_data': f'rv:{submission_id}:accept_c'},
                {'text': '❌ Отклонить с комментарием', 'callback_data': f'rv:{submission_id}:reject_c'},
            ],
            [{'text': 'Отмена', 'callback_data': f'rv:{submission_id}:cancel'}],
        ],
    }


def build_student_profile_url(user_id: int) -> str:
    host = (getattr(settings, 'ALLOWED_HOSTS', []) or ['localhost'])[0]
    scheme = 'http' if host in ('localhost', '127.0.0.1') else 'https'
    return f'{scheme}://{host}/students/{user_id}'
