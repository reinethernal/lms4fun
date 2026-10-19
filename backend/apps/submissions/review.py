from django.utils import timezone

from apps.gamification.services import award_submission_xp
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import Submission


def review_submission(submission: Submission, reviewer, *, status: str, teacher_comment: str = '') -> Submission:
    if status not in (Submission.Status.ACCEPTED, Submission.Status.REJECTED):
        raise ValueError('status must be accepted or rejected')

    if submission.status in (Submission.Status.PENDING, Submission.Status.RUNNING):
        raise ValueError('Дождитесь завершения автопроверки.')

    submission.status = status
    submission.teacher_comment = teacher_comment or ''
    submission.checked_by = reviewer
    submission.checked_at = timezone.now()

    if status == Submission.Status.ACCEPTED:
        submission.score = 100
        submission.xp_awarded = award_submission_xp(submission)
        from apps.gamification.stats import update_stats_on_submission

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
        new_badges = update_stats_on_submission(
            submission.user,
            submission,
            had_prior_failure=had_prior_failure,
        )
        if new_badges:
            from apps.gamification.stats import serialize_awarded_badges

            checker = dict(submission.checker_result or {})
            checker['new_badges'] = serialize_awarded_badges(new_badges)
            checker['message'] = teacher_comment or 'Решение принято преподавателем.'
            submission.checker_result = checker
    else:
        submission.score = 0
        submission.xp_awarded = 0
        message = teacher_comment or 'Решение отклонено. Попробуйте ещё раз.'
        checker = dict(submission.checker_result or {})
        checker['message'] = message
        submission.checker_result = checker
        create_notification(
            submission.user,
            Notification.NotificationType.SUBMISSION_REJECTED,
            'Решение нужно исправить',
            message,
            {'submission_id': submission.id, 'task_id': submission.task_id},
        )

    submission.save()
    return submission
