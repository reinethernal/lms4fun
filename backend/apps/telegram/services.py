from __future__ import annotations

import logging

from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.submissions.access import get_staff_submission, staff_users_for_submission, submissions_queryset_for_staff
from apps.submissions.models import Submission
from apps.submissions.review import review_submission
from apps.submissions.tasks import check_submission_task

from .client import TelegramApiClient, TelegramApiError
from .config import get_telegram_config
from .formatting import (
    escape,
    format_submission_card,
    pending_list_keyboard,
    review_keyboard,
)
from .models import TelegramAccount, TelegramLinkCode

logger = logging.getLogger('apps.telegram')


def telegram_enabled() -> bool:
    return get_telegram_config().is_ready


def get_account_by_chat(chat_id: int) -> TelegramAccount | None:
    return (
        TelegramAccount.objects.select_related('user')
        .filter(chat_id=chat_id, is_active=True)
        .first()
    )


def link_account(code: str, chat_id: int, telegram_username: str = '') -> TelegramAccount:
    link = (
        TelegramLinkCode.objects.select_related('user')
        .filter(code=code.upper().strip())
        .first()
    )
    if link is None or not link.is_valid:
        raise ValueError('Код недействителен или истёк. Создайте новый в админке.')

    user = link.user
    if not (user.is_platform_admin or user.is_teacher):
        raise ValueError('Бот доступен только преподавателям и администраторам.')

    TelegramAccount.objects.filter(chat_id=chat_id).exclude(user=user).update(is_active=False)
    for stale in list(TelegramAccount.objects.filter(chat_id=chat_id).exclude(user=user)):
        stale.chat_id = -(10_000_000 + stale.pk)
        stale.save(update_fields=['chat_id'])

    account, _ = TelegramAccount.objects.update_or_create(
        user=user,
        defaults={
            'chat_id': chat_id,
            'telegram_username': telegram_username or '',
            'is_active': True,
        },
    )

    link.used_at = timezone.now()
    link.save(update_fields=['used_at'])
    return account


def unlink_account(chat_id: int) -> bool:
    updated = TelegramAccount.objects.filter(chat_id=chat_id, is_active=True).update(is_active=False)
    return bool(updated)


def recipients_for_submission(submission: Submission):
    staff = staff_users_for_submission(submission)
    qs = TelegramAccount.objects.select_related('user').filter(
        user__in=staff,
        is_active=True,
    )
    if submission.status == Submission.Status.MANUAL_REVIEW:
        qs = qs.filter(notify_manual_review=True)
    else:
        qs = qs.filter(notify_new_submissions=True)
    return list(qs)


def notify_staff_about_submission(submission_id: int) -> int:
    if not telegram_enabled():
        return 0

    try:
        submission = Submission.objects.select_related(
            'user', 'task', 'task__lesson', 'task__lesson__course', 'language',
        ).get(pk=submission_id)
    except Submission.DoesNotExist:
        return 0

    notify_all = get_telegram_config().notify_all_submissions
    if submission.status == Submission.Status.MANUAL_REVIEW:
        pass
    elif not notify_all:
        return 0

    accounts = recipients_for_submission(submission)
    if not accounts:
        return 0

    client = TelegramApiClient()
    text = format_submission_card(submission, include_code=False)
    if submission.status == Submission.Status.MANUAL_REVIEW:
        text = '🆕 <b>Новое решение на проверке</b>\n\n' + text
        markup = review_keyboard(submission.id)
    else:
        text = '📬 <b>Новое решение</b>\n\n' + text
        markup = review_keyboard(submission.id) if submission.status == Submission.Status.MANUAL_REVIEW else None

    sent = 0
    for account in accounts:
        try:
            client.send_message(account.chat_id, text, reply_markup=markup)
            sent += 1
        except TelegramApiError:
            logger.exception('Failed to notify chat_id=%s about submission %s', account.chat_id, submission_id)
    return sent


def list_pending_for_user(user, limit: int = 10):
    return list(
        submissions_queryset_for_staff(user)
        .filter(status=Submission.Status.MANUAL_REVIEW)[:limit]
    )


def review_via_bot(user, submission_id: int, status: str, comment: str = '') -> Submission:
    submission = get_staff_submission(user, submission_id)
    if submission is None:
        raise ValueError('Решение не найдено или нет доступа.')
    submission = review_submission(submission, user, status=status, teacher_comment=comment)
    if comment.strip():
        create_notification(
            submission.user,
            Notification.NotificationType.TEACHER_COMMENT,
            'Комментарий преподавателя',
            comment.strip(),
            {'submission_id': submission.id, 'task_id': submission.task_id},
        )
    return submission


def recheck_via_bot(user, submission_id: int) -> Submission:
    submission = get_staff_submission(user, submission_id)
    if submission is None:
        raise ValueError('Решение не найдено или нет доступа.')
    if submission.status in (Submission.Status.PENDING, Submission.Status.RUNNING):
        raise ValueError('Проверка уже выполняется.')
    submission.status = Submission.Status.PENDING
    submission.checked_at = None
    submission.checked_by = None
    submission.save(update_fields=['status', 'checked_at', 'checked_by'])
    check_submission_task.delay(submission.id)
    return submission


def open_submission_for_user(user, submission_id: int) -> Submission:
    submission = get_staff_submission(user, submission_id)
    if submission is None:
        raise ValueError('Решение не найдено или нет доступа.')
    return submission


def format_pending_message(user) -> tuple[str, dict | None]:
    pending = list_pending_for_user(user)
    if not pending:
        return 'Нет решений на проверке.', None
    lines = [f'<b>На проверке: {len(pending)}</b>', '']
    items = []
    for sub in pending:
        student = sub.user.display_name or sub.user.username
        title = f'#{sub.id} {student} — {sub.task.title}'
        items.append((sub.id, title))
        lines.append(f'• {escape_title(title)}')
    lines.append('')
    lines.append('Нажми на решение, чтобы открыть.')
    return '\n'.join(lines), pending_list_keyboard(items)


def escape_title(text: str) -> str:
    return escape(text)
