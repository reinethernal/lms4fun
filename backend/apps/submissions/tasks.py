from celery import shared_task
from django.utils import timezone

import logging

logger = logging.getLogger('apps.submissions')


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def check_submission_task(self, submission_id: int):
    from apps.gamification.services import award_submission_xp
    from apps.submissions.checker import evaluate_submission
    from apps.submissions.models import Submission

    try:
        submission = Submission.objects.select_related('task', 'task__language', 'user').get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.warning('Submission %s not found for check', submission_id)
        return

    logger.info(
        'Checking submission id=%s user=%s task=%s',
        submission_id,
        submission.user_id,
        submission.task_id,
    )

    submission.status = Submission.Status.RUNNING
    submission.save(update_fields=['status'])

    try:
        result = evaluate_submission(submission.task, submission.code, user=submission.user)
    except Exception as exc:
        logger.exception('Submission %s evaluation failed', submission_id)
        submission.status = Submission.Status.RUNTIME_ERROR
        submission.checker_result = {'error': str(exc)}
        submission.checked_at = timezone.now()
        submission.save()
        raise self.retry(exc=exc)

    submission.status = result['status']
    submission.checker_result = result
    if result.get('details'):
        last = result['details'][-1]
        submission.stdout = last.get('stdout', '')
        submission.stderr = last.get('stderr', '')
        submission.compile_output = last.get('compile_output', '')
    submission.checked_at = timezone.now()

    had_prior_failure = Submission.objects.filter(
        user=submission.user,
        task=submission.task,
        status__in=[
            Submission.Status.WRONG_ANSWER,
            Submission.Status.RUNTIME_ERROR,
            Submission.Status.COMPILE_ERROR,
            Submission.Status.TIME_LIMIT,
            Submission.Status.REJECTED,
        ],
    ).exclude(pk=submission.pk).exists()

    if submission.status == Submission.Status.ACCEPTED:
        from apps.gamification.stats import update_stats_on_submission

        new_badges = update_stats_on_submission(submission.user, submission, had_prior_failure=had_prior_failure)
        submission.score = 100
        submission.xp_awarded = award_submission_xp(submission)
    else:
        submission.score = 0
        submission.xp_awarded = 0
        from apps.gamification.stats import update_stats_on_submission

        new_badges = update_stats_on_submission(submission.user, submission, had_prior_failure=had_prior_failure)
        if submission.status in (
            Submission.Status.WRONG_ANSWER,
            Submission.Status.RUNTIME_ERROR,
            Submission.Status.COMPILE_ERROR,
            Submission.Status.TIME_LIMIT,
            Submission.Status.REJECTED,
        ):
            from apps.notifications.models import Notification
            from apps.notifications.services import create_notification

            create_notification(
                submission.user,
                Notification.NotificationType.SUBMISSION_REJECTED,
                'Решение нужно исправить',
                result.get('message', 'Попробуй ещё раз.'),
                {'submission_id': submission.id, 'task_id': submission.task_id},
            )

    if new_badges:
        from apps.gamification.stats import serialize_awarded_badges

        checker = dict(submission.checker_result or {})
        checker['new_badges'] = serialize_awarded_badges(new_badges)
        submission.checker_result = checker

    submission.save()
    logger.info(
        'Submission id=%s checked status=%s score=%s',
        submission_id,
        submission.status,
        submission.score,
    )

    try:
        from apps.telegram.tasks import notify_staff_submission_task

        notify_staff_submission_task.delay(submission.id)
    except Exception:
        logger.exception('Failed to enqueue telegram notify for submission %s', submission_id)

    return submission.status
