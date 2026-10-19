from django.db.models import Sum

from apps.accounts.models import Group, User
from apps.accounts.parent_access import ensure_parent_child
from apps.gamification.models import UserBadge, UserProgress
from apps.gamification.services import get_leaderboard
from apps.gamification.stats import recalculate_aggregate_stats
from apps.submissions.models import Submission


def teacher_has_student(viewer: User, student: User) -> bool:
    if not viewer.is_teacher:
        return False
    return Group.objects.filter(
        teacher=viewer,
        memberships__user=student,
    ).exists()


def can_view_student_profile(viewer: User, student: User) -> bool:
    if student.role != User.Role.STUDENT:
        return False
    if viewer.id == student.id:
        return True
    if viewer.is_platform_admin:
        return True
    if viewer.is_parent:
        try:
            ensure_parent_child(viewer, student.id)
            return True
        except PermissionError:
            return False
    if teacher_has_student(viewer, student):
        return True
    return False


def get_profile_permissions(viewer: User, student: User) -> dict:
    is_self = viewer.id == student.id
    return {
        'can_edit': is_self,
        'can_manage_badges': viewer.is_platform_admin and student.role == User.Role.STUDENT,
        'can_view_submissions': can_view_student_profile(viewer, student),
    }


def _student_rank(student: User) -> int | None:
    for entry in get_leaderboard(limit=500):
        if entry['user_id'] == student.id:
            return entry['rank']
    return None


def _skill_highlights(student: User) -> dict:
    stats = recalculate_aggregate_stats(student)
    highlights = {
        'total_xp': stats.get('total_xp', 0),
        'tasks_completed': stats.get('tasks_completed', 0),
        'lessons_completed': stats.get('lessons_completed', 0),
        'code_runs_success': stats.get('code_runs_success', 0),
        'bugs_fixed': stats.get('bugs_fixed', 0),
    }
    skills = stats.get('skills') or {}
    if isinstance(skills, dict) and skills:
        top = sorted(skills.items(), key=lambda item: item[1], reverse=True)[:5]
        highlights['top_skills'] = [{'name': name, 'level': level} for name, level in top]
    return highlights


def build_student_profile(student: User, viewer: User, request=None) -> dict:
    from apps.gamification.serializers import UserBadgeSerializer, UserProgressSerializer
    from apps.submissions.serializers import AdminSubmissionListSerializer

    from .avatar import user_avatar_url
    from .serializers import UserSerializer

    progress = UserProgress.objects.filter(user=student).select_related('course', 'lesson', 'task')
    badges = UserBadge.objects.filter(user=student).select_related('badge', 'awarded_by')
    submissions = (
        Submission.objects.filter(user=student)
        .select_related('user', 'task', 'language')
        .order_by('-submitted_at')[:20]
    )

    agg = progress.aggregate(
        total_xp=Sum('xp_earned'),
        tasks_completed=Sum('tasks_completed'),
        lessons_completed=Sum('lessons_completed'),
    )

    context = {'request': request} if request else {}
    user_data = UserSerializer(student, context=context).data
    user_data.pop('children', None)
    user_data['avatar'] = user_avatar_url(student, request)

    return {
        'user': user_data,
        'stats': {
            'total_xp': agg['total_xp'] or 0,
            'tasks_completed': agg['tasks_completed'] or 0,
            'lessons_completed': agg['lessons_completed'] or 0,
            'badges_count': badges.count(),
            'rank': _student_rank(student),
        },
        'progress': UserProgressSerializer(progress, many=True).data,
        'badges': UserBadgeSerializer(badges, many=True, context=context).data,
        'skill_highlights': _skill_highlights(student),
        'recent_submissions': AdminSubmissionListSerializer(submissions, many=True).data,
        'permissions': get_profile_permissions(viewer, student),
    }


def build_self_profile(user: User, request=None) -> dict:
    if user.role == User.Role.STUDENT:
        return build_student_profile(user, user, request=request)

    from .serializers import UserSerializer

    context = {'request': request} if request else {}
    return {
        'user': UserSerializer(user, context=context).data,
        'stats': {
            'total_xp': 0,
            'tasks_completed': 0,
            'lessons_completed': 0,
            'badges_count': 0,
            'rank': None,
        },
        'progress': [],
        'badges': [],
        'skill_highlights': {},
        'recent_submissions': [],
        'permissions': {
            'can_edit': True,
            'can_manage_badges': False,
            'can_view_submissions': False,
        },
    }
