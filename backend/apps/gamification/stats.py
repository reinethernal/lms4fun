from django.db.models import Sum

from apps.submissions.models import CodeRun, Submission

from .code_analyzer import analyze_code, detect_error_types, merge_skill_stats
from .models import UserProgress, UserSkillStats, XPTransaction


def default_stats() -> dict:
    return {
        'code_runs_success': 0,
        'tasks_completed': 0,
        'lessons_completed': 0,
        'total_xp': 0,
        'language_xp': {},
        'language_started': [],
        'tasks_by_slug': {},
        'projects_completed': [],
        'skills': {},
        'bugs_fixed': 0,
        'syntax_errors_fixed': 0,
        'name_errors_fixed': 0,
        'indentation_errors_fixed': 0,
        'task_errors_before_success': {},
        'final_project_started': 0,
        'final_project_submitted': 0,
        'final_project_runs_success': 0,
        'final_project_accepted': 0,
        'final_project_improvements': 0,
        'challenges_won': 0,
        'helped_user': 0,
        'code_explained': 0,
    }


def get_user_stats(user) -> UserSkillStats:
    stats, _ = UserSkillStats.objects.get_or_create(user=user, defaults={'stats_json': default_stats()})
    if not stats.stats_json:
        stats.stats_json = default_stats()
        stats.save(update_fields=['stats_json'])
    return stats


def recalculate_aggregate_stats(user) -> dict:
    stats_obj = get_user_stats(user)
    data = {**default_stats(), **stats_obj.stats_json}

    data['total_xp'] = UserProgress.objects.filter(user=user).aggregate(t=Sum('xp_earned'))['t'] or 0
    data['tasks_completed'] = UserProgress.objects.filter(user=user).aggregate(t=Sum('tasks_completed'))['t'] or 0
    data['lessons_completed'] = UserProgress.objects.filter(user=user).aggregate(t=Sum('lessons_completed'))['t'] or 0

    lang_xp: dict[str, int] = {}
    started: set[str] = set(data.get('language_started', []))
    for row in XPTransaction.objects.filter(user=user).select_related('language'):
        if row.language:
            slug = row.language.slug
            lang_xp[slug] = lang_xp.get(slug, 0) + row.amount
            started.add(slug)
    data['language_xp'] = lang_xp
    data['language_started'] = sorted(started)

    stats_obj.stats_json = data
    stats_obj.save(update_fields=['stats_json', 'updated_at'])
    return data


def serialize_awarded_badges(badges, request=None) -> list[dict]:
    from .serializers import BadgeAwardSerializer

    return BadgeAwardSerializer(badges, many=True, context={'request': request}).data


def update_stats_on_code_run(user, code_run: CodeRun) -> list:
    stats_obj = get_user_stats(user)
    data = {**default_stats(), **stats_obj.stats_json}

    if code_run.status == CodeRun.Status.SUCCESS:
        data['code_runs_success'] = data.get('code_runs_success', 0) + 1
        slug = code_run.language.slug if code_run.language_id else 'python'
        started = set(data.get('language_started', []))
        started.add(slug)
        data['language_started'] = sorted(started)
        if slug == 'javascript' and 'console.log' in (code_run.source_code or ''):
            skills = data.get('skills', {})
            skills['js_console_log_success'] = skills.get('js_console_log_success', 0) + 1
            data['skills'] = skills

    analysis = analyze_code(code_run.source_code, code_run.language.slug if code_run.language_id else 'python')
    data = merge_skill_stats(data, analysis)

    stats_obj.stats_json = data
    stats_obj.save(update_fields=['stats_json', 'updated_at'])
    recalculate_aggregate_stats(user)

    from .badge_evaluator import check_and_award_badges

    return check_and_award_badges(user)


def _record_task_error(user, task_id: int, error_types: list[str]) -> None:
    stats_obj = get_user_stats(user)
    data = {**default_stats(), **stats_obj.stats_json}
    errors_map = dict(data.get('task_errors_before_success', {}))
    entry = errors_map.get(str(task_id), [])
    for err in error_types:
        if err not in entry:
            entry.append(err)
    errors_map[str(task_id)] = entry
    data['task_errors_before_success'] = errors_map
    stats_obj.stats_json = data
    stats_obj.save(update_fields=['stats_json', 'updated_at'])


def _maybe_lesson_completed(user, lesson) -> None:
    from apps.lessons.progress import is_lesson_completed

    if not is_lesson_completed(user, lesson):
        return
    progress = UserProgress.objects.filter(user=user, course=lesson.course).first()
    if progress:
        progress.lessons_completed = max(progress.lessons_completed, lesson.number)
        progress.save(update_fields=['lessons_completed'])


def update_stats_on_submission(user, submission: Submission, *, had_prior_failure: bool = False) -> list:
    stats_obj = get_user_stats(user)
    data = {**default_stats(), **stats_obj.stats_json}
    task = submission.task
    lang_slug = submission.language.slug if submission.language_id else 'python'

    if submission.status != Submission.Status.ACCEPTED:
        error_types = detect_error_types(submission.stderr, submission.compile_output)
        if error_types:
            _record_task_error(user, task.id, error_types)
        stats_obj.stats_json = data
        stats_obj.save(update_fields=['stats_json', 'updated_at'])
        return []

    slug = task.slug or f'task-{task.id}'
    tasks_by_slug = dict(data.get('tasks_by_slug', {}))
    tasks_by_slug[slug] = tasks_by_slug.get(slug, 0) + 1
    data['tasks_by_slug'] = tasks_by_slug

    if task.task_type in ('project', 'challenge'):
        projects = list(data.get('projects_completed', []))
        project_slug = slug
        if project_slug not in projects:
            projects.append(project_slug)
        data['projects_completed'] = projects

    if had_prior_failure:
        data['bugs_fixed'] = data.get('bugs_fixed', 0) + 1
        errors_map = data.get('task_errors_before_success', {})
        for err in errors_map.get(str(task.id), []):
            if err == 'syntax_error':
                data['syntax_errors_fixed'] = data.get('syntax_errors_fixed', 0) + 1
            elif err == 'name_error':
                data['name_errors_fixed'] = data.get('name_errors_fixed', 0) + 1
            elif err == 'indentation_error':
                data['indentation_errors_fixed'] = data.get('indentation_errors_fixed', 0) + 1

    analysis = analyze_code(submission.code, lang_slug)
    data = merge_skill_stats(data, analysis)

    skills = data.get('skills', {})
    if 'input' in submission.code:
        skills['input_tasks_completed'] = skills.get('input_tasks_completed', 0) + 1
    if re_if_else(submission.code):
        skills['if_else_tasks_completed'] = skills.get('if_else_tasks_completed', 0) + 1
    if 'for' in submission.code:
        skills['for_tasks_completed'] = skills.get('for_tasks_completed', 0) + 1
    if 'while' in submission.code:
        skills['while_tasks_completed'] = skills.get('while_tasks_completed', 0) + 1
    if 'random' in submission.code:
        skills['random_tasks_completed'] = skills.get('random_tasks_completed', 0) + 1
    if task.task_type == 'challenge' and submission.status == Submission.Status.ACCEPTED:
        data['challenges_won'] = data.get('challenges_won', 0) + 1

    if 'final' in slug or 'финал' in task.title.lower():
        data['final_project_submitted'] = data.get('final_project_submitted', 0) + 1
        data['final_project_accepted'] = data.get('final_project_accepted', 0) + 1

    data['skills'] = skills
    stats_obj.stats_json = data
    stats_obj.save(update_fields=['stats_json', 'updated_at'])

    _maybe_lesson_completed(user, task.lesson)
    recalculate_aggregate_stats(user)

    from .badge_evaluator import check_and_award_badges

    return check_and_award_badges(user)


def re_if_else(code: str) -> bool:
    import re
    return bool(re.search(r'\bif\b', code) and re.search(r'\belse\b', code))
