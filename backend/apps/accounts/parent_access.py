from apps.accounts.models import User
from apps.submissions.models import Submission


def parent_child_ids(user: User) -> list[int]:
    if not user.is_parent:
        return []
    return list(user.children.values_list('id', flat=True))


def ensure_parent_child(user: User, child_id: int) -> User:
    if not user.is_parent:
        raise PermissionError('Только для родителей.')
    child = User.objects.filter(pk=child_id, role=User.Role.STUDENT).first()
    if child is None or not user.children.filter(pk=child_id).exists():
        raise PermissionError('Нет доступа к этому ученику.')
    return child


def can_view_submission(user: User, submission: Submission) -> bool:
    if submission.user_id == user.id:
        return True
    if user.is_platform_admin or user.is_teacher:
        return True
    if user.is_parent and user.children.filter(pk=submission.user_id).exists():
        return True
    return False
