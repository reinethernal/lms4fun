from django.db.models import Sum

from apps.submissions.models import Submission

from .models import Badge, UserBadge, UserProgress, XPTransaction


def award_submission_xp(submission: Submission) -> int:
    """Award XP for accepted submission if not already awarded for this task."""
    existing = Submission.objects.filter(
        user=submission.user,
        task=submission.task,
        status=Submission.Status.ACCEPTED,
    ).exclude(pk=submission.pk).exists()
    if existing:
        return 0

    amount = submission.task.max_xp
    course = submission.task.lesson.course

    progress, _ = UserProgress.objects.get_or_create(
        user=submission.user,
        course=course,
        defaults={'lesson': submission.task.lesson, 'task': submission.task},
    )
    progress.xp_earned += amount
    progress.tasks_completed += 1
    progress.lesson = submission.task.lesson
    progress.task = submission.task
    progress.save()

    XPTransaction.objects.create(
        user=submission.user,
        course=course,
        lesson=submission.task.lesson,
        task=submission.task,
        language=submission.language,
        amount=amount,
        reason=f'Задание: {submission.task.title}',
    )

    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification

    create_notification(
        submission.user,
        Notification.NotificationType.XP_EARNED,
        f'+{amount} XP',
        f'Задание «{submission.task.title}» выполнено.',
        {'task_id': submission.task_id, 'amount': amount},
    )
    create_notification(
        submission.user,
        Notification.NotificationType.SUBMISSION_ACCEPTED,
        'Решение принято',
        'Отлично! Программа работает.',
        {'submission_id': submission.id, 'task_id': submission.task_id},
    )

    return amount


def award_badge_to_user(user, badge: Badge, awarded_by) -> UserBadge:
    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification

    user_badge, created = UserBadge.objects.get_or_create(
        user=user,
        badge=badge,
        defaults={'awarded_by': awarded_by},
    )
    if not created:
        raise ValueError('Бейдж уже выдан этому ученику.')
    create_notification(
        user,
        Notification.NotificationType.BADGE_EARNED,
        f'Бейдж: {badge.title}',
        badge.description,
        {'badge_id': badge.id, 'manual': True},
    )
    return user_badge


def revoke_badge_from_user(user, badge_id: int) -> None:
    deleted, _ = UserBadge.objects.filter(user=user, badge_id=badge_id).delete()
    if not deleted:
        raise ValueError('Бейдж не найден у этого ученика.')


def get_leaderboard(course_id=None, group_id=None, limit=50, request=None):
    from django.contrib.auth import get_user_model
    from django.db.models import Sum

    from apps.accounts.avatar import user_avatar_url

    User = get_user_model()

    progress_qs = UserProgress.objects.filter(
        user__role=User.Role.STUDENT,
        user__is_active=True,
    )
    if group_id:
        progress_qs = progress_qs.filter(user__group_memberships__group_id=group_id)
    if course_id:
        progress_qs = progress_qs.filter(course_id=course_id)

    rows = (
        progress_qs.values(
            'user_id',
            'user__username',
            'user__display_name',
            'user__avatar',
        )
        .annotate(
            total_xp=Sum('xp_earned'),
            tasks_completed=Sum('tasks_completed'),
        )
        .filter(total_xp__gt=0)
        .order_by('-total_xp', '-tasks_completed', 'user__username')
    )

    entries = []
    user_ids = [row['user_id'] for row in rows[:limit]]
    users = {u.id: u for u in User.objects.filter(id__in=user_ids)}
    for rank, row in enumerate(rows[:limit], start=1):
        user = users.get(row['user_id'])
        entries.append({
            'rank': rank,
            'user_id': row['user_id'],
            'username': row['user__username'],
            'display_name': row['user__display_name'] or row['user__username'],
            'avatar': user_avatar_url(user, request) if user else row['user__avatar'] or '',
            'total_xp': row['total_xp'] or 0,
            'tasks_completed': row['tasks_completed'] or 0,
        })
    return entries
