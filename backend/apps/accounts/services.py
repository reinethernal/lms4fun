from django.db import transaction

from apps.gamification.stats import default_stats


GAMIFICATION_NOTIFICATION_TYPES = [
    'lesson_completed',
    'badge_earned',
    'submission_accepted',
    'submission_rejected',
    'lesson_unlocked',
    'xp_earned',
]


@transaction.atomic
def purge_user_ranking_data(user) -> None:
    """Remove all leaderboard-related records for a user before account deletion."""
    from apps.gamification.models import UserBadge, UserProgress, UserSkillStats, XPTransaction
    from apps.notifications.models import Notification
    from apps.submissions.models import CodeRun, Submission

    user_id = user.pk
    UserProgress.objects.filter(user_id=user_id).delete()
    XPTransaction.objects.filter(user_id=user_id).delete()
    UserBadge.objects.filter(user_id=user_id).delete()
    UserSkillStats.objects.filter(user_id=user_id).delete()
    Submission.objects.filter(user_id=user_id).delete()
    CodeRun.objects.filter(user_id=user_id).delete()
    Notification.objects.filter(user_id=user_id).delete()


@transaction.atomic
def reset_student_statistics(user, *, include_submissions: bool = False) -> dict:
    """Reset gamification data for a student. Optionally wipe submissions and code runs."""
    from apps.accounts.models import User
    from apps.gamification.models import UserBadge, UserProgress, UserSkillStats, XPTransaction
    from apps.notifications.models import Notification
    from apps.submissions.models import CodeRun, Submission

    if user.role != User.Role.STUDENT:
        raise ValueError('Сброс статистики доступен только для учеников.')

    user_id = user.pk
    progress_deleted = UserProgress.objects.filter(user_id=user_id).delete()[0]
    xp_deleted = XPTransaction.objects.filter(user_id=user_id).delete()[0]
    badges_deleted = UserBadge.objects.filter(user_id=user_id).delete()[0]
    notifications_deleted = Notification.objects.filter(
        user_id=user_id,
        notification_type__in=GAMIFICATION_NOTIFICATION_TYPES,
    ).delete()[0]

    UserSkillStats.objects.update_or_create(
        user=user,
        defaults={'stats_json': default_stats()},
    )

    submissions_cleared = 0
    code_runs_cleared = 0

    if include_submissions:
        submissions_cleared = Submission.objects.filter(user_id=user_id).delete()[0]
        code_runs_cleared = CodeRun.objects.filter(user_id=user_id).delete()[0]
    else:
        submissions_cleared = Submission.objects.filter(user_id=user_id).update(xp_awarded=0)

    return {
        'include_submissions': include_submissions,
        'progress_deleted': progress_deleted,
        'xp_transactions_deleted': xp_deleted,
        'badges_deleted': badges_deleted,
        'notifications_deleted': notifications_deleted,
        'submissions_affected': submissions_cleared,
        'code_runs_deleted': code_runs_cleared,
    }


@transaction.atomic
def delete_user_account(user) -> None:
    """Delete user and all ranking/progress data."""
    user.children.clear()
    user.parents.clear()
    user.delete()
