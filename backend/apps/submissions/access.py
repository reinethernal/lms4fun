from apps.accounts.models import Group, User
from apps.submissions.models import Submission


def submissions_queryset_for_staff(user, request=None):
    qs = Submission.objects.select_related(
        'user', 'task', 'task__lesson', 'task__lesson__course', 'language', 'checked_by',
    ).order_by('-submitted_at')

    if user.is_platform_admin:
        pass
    elif user.is_teacher:
        student_ids = Group.objects.filter(teacher=user).values_list('memberships__user_id', flat=True)
        qs = qs.filter(user_id__in=student_ids)
    else:
        return qs.none()

    if request is not None:
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        course_id = request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(task__lesson__course_id=course_id)
        lesson_id = request.query_params.get('lesson_id')
        if lesson_id:
            qs = qs.filter(task__lesson_id=lesson_id)
        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)
        task_id = request.query_params.get('task_id')
        if task_id:
            qs = qs.filter(task_id=task_id)

    return qs


def get_staff_submission(user, pk: int) -> Submission | None:
    return (
        submissions_queryset_for_staff(user)
        .select_related('user', 'task', 'language', 'checked_by')
        .filter(pk=pk)
        .first()
    )


def staff_can_access_submission(user, submission: Submission) -> bool:
    if user.is_platform_admin:
        return True
    if not user.is_teacher:
        return False
    return Group.objects.filter(teacher=user, memberships__user_id=submission.user_id).exists()


def staff_users_for_submission(submission: Submission):
    """Teachers of the student's groups plus platform admins."""
    teacher_ids = Group.objects.filter(
        memberships__user_id=submission.user_id,
        teacher__isnull=False,
    ).values_list('teacher_id', flat=True)
    teachers = User.objects.filter(id__in=teacher_ids, role=User.Role.TEACHER)
    admins = User.objects.filter(
        role__in=[User.Role.SUPERADMIN, User.Role.ADMIN],
    ) | User.objects.filter(is_superuser=True)
    return (teachers | admins).distinct()
