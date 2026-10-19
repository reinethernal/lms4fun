from apps.submissions.models import Submission
from apps.tasks.demo import is_run_only_task
from apps.tasks.models import Task

from .models import Lesson


def bypass_lesson_lock(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return (
        user.is_platform_admin
        or user.is_teacher
        or user.is_parent
        or user.is_superadmin
    )


def is_lesson_completed(user, lesson: Lesson) -> bool:
    required = Task.objects.filter(lesson=lesson, is_required=True)
    required_ids = [task.id for task in required if not is_run_only_task(task)]
    if not required_ids:
        return True
    accepted = Submission.objects.filter(
        user=user,
        task__lesson=lesson,
        status=Submission.Status.ACCEPTED,
    ).values_list('task_id', flat=True).distinct()
    return set(required_ids).issubset(set(accepted))


def is_lesson_in_review(user, lesson: Lesson) -> bool:
    """True when all required tasks are submitted and at least one awaits manual review."""
    if is_lesson_completed(user, lesson):
        return False

    required = Task.objects.filter(lesson=lesson, is_required=True)
    required_ids = [task.id for task in required if not is_run_only_task(task)]
    if not required_ids:
        return False

    has_manual_review = False
    for task_id in required_ids:
        if Submission.objects.filter(
            user=user,
            task_id=task_id,
            status=Submission.Status.ACCEPTED,
        ).exists():
            continue

        latest = (
            Submission.objects.filter(user=user, task_id=task_id)
            .order_by('-submitted_at', '-id')
            .first()
        )
        if not latest:
            return False
        if latest.status == Submission.Status.MANUAL_REVIEW:
            has_manual_review = True
            continue
        return False

    return has_manual_review


def ordered_course_lessons(course):
    return Lesson.objects.filter(
        course=course,
        status=Lesson.Status.PUBLISHED,
    ).order_by('sort_order', 'number', 'id')


def is_lesson_locked_for_user(user, lesson: Lesson) -> bool:
    if bypass_lesson_lock(user):
        return False
    lessons = list(ordered_course_lessons(lesson.course))
    if not lessons:
        return False
    if lessons[0].id == lesson.id:
        return False
    for idx, item in enumerate(lessons):
        if item.id == lesson.id:
            if idx == 0:
                return False
            return not is_lesson_completed(user, lessons[idx - 1])
    return True


def get_lesson_unlock_map(user, course) -> dict[int, dict[str, bool]]:
    lessons = list(ordered_course_lessons(course))
    result: dict[int, dict[str, bool]] = {}
    for idx, lesson in enumerate(lessons):
        completed = is_lesson_completed(user, lesson)
        if bypass_lesson_lock(user):
            locked = False
        elif idx == 0:
            locked = False
        else:
            locked = not is_lesson_completed(user, lessons[idx - 1])
        result[lesson.id] = {
            'is_completed': completed,
            'is_locked': locked,
            'is_in_review': is_lesson_in_review(user, lesson),
        }
    return result
