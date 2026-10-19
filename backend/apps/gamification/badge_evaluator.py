from .models import Badge, UserBadge
from .stats import get_user_stats, recalculate_aggregate_stats


def _get_stat(stats: dict, key: str, default=0):
    return stats.get(key, default)


def _skill_count(stats: dict, key: str) -> int:
    return int(stats.get('skills', {}).get(key, 0))


def _language_xp(stats: dict, language: str) -> int:
    return int(stats.get('language_xp', {}).get(language, 0))


def _language_started(stats: dict, language: str) -> bool:
    return language in stats.get('language_started', [])


def _task_slug_done(stats: dict, slug: str) -> bool:
    return stats.get('tasks_by_slug', {}).get(slug, 0) > 0


def _project_done(stats: dict, slug: str) -> bool:
    return slug in stats.get('projects_completed', [])


def evaluate_badge(stats: dict, badge: Badge) -> bool:
    key = badge.effective_condition_key()
    value = badge.condition_value or 0
    params = badge.condition_params or {}

    if not key or key == 'manual':
        return False

    if key in ('xp_total', 'total_xp'):
        return _get_stat(stats, 'total_xp') >= value
    if key == 'tasks_completed':
        return _get_stat(stats, 'tasks_completed') >= value
    if key == 'lessons_completed':
        return _get_stat(stats, 'lessons_completed') >= value
    if key == 'code_runs_success':
        return _get_stat(stats, 'code_runs_success') >= value

    if key == 'language_started':
        return _language_started(stats, params.get('language', 'python'))
    if key == 'language_xp':
        return _language_xp(stats, params.get('language', 'python')) >= value

    if key == 'successful_task':
        return _task_slug_done(stats, params.get('task_slug', ''))
    if key == 'lesson_skill_completed':
        skill = params.get('skill', 'print')
        return _skill_count(stats, f'{skill}_used') >= value or _skill_count(stats, 'print_used') >= value

    if key == 'string_tasks_completed':
        return _skill_count(stats, 'string_tasks') >= value
    if key == 'variables_used':
        return _skill_count(stats, 'variables_used') >= value
    if key == 'arithmetic_tasks_completed':
        return _skill_count(stats, 'arithmetic_plus_used') >= value
    if key == 'input_tasks_completed':
        return _skill_count(stats, 'input_tasks_completed') >= value
    if key == 'numbers_tasks_completed':
        return _skill_count(stats, 'numbers_tasks') >= value
    if key == 'arithmetic_operator_used':
        op = params.get('operator', '+')
        if op == '+':
            return _skill_count(stats, 'arithmetic_plus_used') >= value
        if op == '*':
            return _skill_count(stats, 'arithmetic_mul_used') >= value
        return False
    if key == 'if_else_tasks_completed':
        return _skill_count(stats, 'if_else_tasks_completed') >= value
    if key == 'conditional_tasks_completed':
        return _skill_count(stats, 'if_else_tasks_completed') >= value
    if key == 'elif_used':
        return _skill_count(stats, 'elif_used') >= value
    if key == 'logical_and_used':
        return _skill_count(stats, 'logical_and_used') >= value
    if key == 'logical_or_used':
        return _skill_count(stats, 'logical_or_used') >= value
    if key == 'random_used':
        return _skill_count(stats, 'random_used') >= value
    if key == 'random_tasks_completed':
        return _skill_count(stats, 'random_tasks_completed') >= value
    if key == 'random_max_roll_hit':
        return _skill_count(stats, 'random_used') >= value
    if key == 'while_used':
        return _skill_count(stats, 'while_used') >= value
    if key == 'while_tasks_completed':
        return _skill_count(stats, 'while_tasks_completed') >= value
    if key == 'infinite_loop_fixed':
        return _get_stat(stats, 'bugs_fixed') >= value
    if key == 'break_used':
        return _skill_count(stats, 'break_used') >= value
    if key == 'for_used':
        return _skill_count(stats, 'for_used') >= value
    if key == 'for_tasks_completed':
        return _skill_count(stats, 'for_tasks_completed') >= value
    if key == 'list_created':
        return _skill_count(stats, 'list_created') >= value
    if key == 'append_used':
        return _skill_count(stats, 'append_used') >= value
    if key == 'remove_used':
        return _skill_count(stats, 'remove_used') >= value
    if key == 'in_operator_used':
        return _skill_count(stats, 'in_operator_used') >= value
    if key == 'list_items_total':
        return _skill_count(stats, 'append_used') >= value
    if key == 'custom_changes_added':
        return _skill_count(stats, 'custom_changes_added') >= value
    if key == 'function_created':
        return _skill_count(stats, 'functions_created') >= value
    if key == 'functions_created':
        return _skill_count(stats, 'functions_created') >= value
    if key == 'function_parameters_used':
        return _skill_count(stats, 'function_parameters_used') >= value
    if key == 'return_used':
        return _skill_count(stats, 'return_used') >= value
    if key == 'bug_fixed':
        return _get_stat(stats, 'bugs_fixed') >= value
    if key == 'syntax_error_fixed':
        return _get_stat(stats, 'syntax_errors_fixed') >= value
    if key == 'name_error_fixed':
        return _get_stat(stats, 'name_errors_fixed') >= value
    if key == 'indentation_error_fixed':
        return _get_stat(stats, 'indentation_errors_fixed') >= value
    if key == 'comment_added':
        return _skill_count(stats, 'comment_added') >= value
    if key == 'comments_added':
        return _skill_count(stats, 'comment_added') >= value
    if key == 'clean_code_score':
        return _skill_count(stats, 'clean_code_score') >= value
    if key == 'project_completed':
        return _project_done(stats, params.get('project_slug', ''))
    if key == 'guess_number_won':
        return _project_done(stats, 'guess_number_basic') and value <= _get_stat(stats, 'challenges_won')
    if key == 'added_hint_logic':
        return _skill_count(stats, 'if_else_tasks_completed') >= value
    if key == 'shop_items_created':
        return _skill_count(stats, 'list_created') >= value
    if key == 'shop_balance_configured':
        return _project_done(stats, 'shop_basic')
    if key == 'rewards_logic_added':
        return _skill_count(stats, 'if_else_tasks_completed') >= value
    if key == 'challenges_won':
        return _get_stat(stats, 'challenges_won') >= value
    if key == 'final_project_started':
        return _get_stat(stats, 'final_project_started') >= value
    if key == 'final_project_submitted':
        return _get_stat(stats, 'final_project_submitted') >= value
    if key == 'final_project_runs_success':
        return _get_stat(stats, 'final_project_runs_success') >= value
    if key == 'final_project_accepted':
        return _get_stat(stats, 'final_project_accepted') >= value
    if key == 'final_project_improvements':
        return _get_stat(stats, 'final_project_improvements') >= value
    if key == 'java_compiles_success':
        return _skill_count(stats, 'java_compiles_success') >= value
    if key == 'js_console_log_success':
        return _skill_count(stats, 'js_console_log_success') >= value
    if key == 'code_explained':
        return _get_stat(stats, 'code_explained') >= value
    if key == 'helped_user':
        return _get_stat(stats, 'helped_user') >= value

    return False


def check_and_award_badges(user) -> list[Badge]:
    stats = recalculate_aggregate_stats(user)
    awarded = []

    for badge in Badge.objects.filter(is_active=True):
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue
        if not evaluate_badge(stats, badge):
            continue
        UserBadge.objects.create(user=user, badge=badge)
        awarded.append(badge)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification

        create_notification(
            user,
            Notification.NotificationType.BADGE_EARNED,
            f'Бейдж: {badge.title}',
            badge.description,
            {'badge_id': badge.id},
        )

    return awarded
