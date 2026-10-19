from celery import shared_task

import logging

logger = logging.getLogger('apps.telegram')


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def notify_staff_submission_task(self, submission_id: int):
    from .services import notify_staff_about_submission, telegram_enabled

    if not telegram_enabled():
        return 0
    try:
        return notify_staff_about_submission(submission_id)
    except Exception as exc:
        logger.exception('Telegram notify failed for submission %s', submission_id)
        raise self.retry(exc=exc)
