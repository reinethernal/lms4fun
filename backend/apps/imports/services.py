import json
import re
import zipfile
from io import BytesIO
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.courses.models import Course, ProgrammingLanguage
from apps.lessons.models import Lesson
from apps.tasks.models import Task

from .models import ImportJob


class ImportServiceError(Exception):
    pass


def _get_language(slug_or_name: str) -> ProgrammingLanguage:
    lang = ProgrammingLanguage.objects.filter(slug=slug_or_name).first()
    if not lang:
        lang = ProgrammingLanguage.objects.filter(name__iexact=slug_or_name).first()
    if not lang:
        raise ImportServiceError(f'Язык не найден: {slug_or_name}')
    return lang


def _unique_slug(model, base_slug: str, **filters) -> str:
    slug = base_slug or 'item'
    counter = 1
    while model.objects.filter(slug=slug, **filters).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    return slug


def _map_checker_type(raw: str) -> str:
    mapping = {
        'stdout_exact': Task.CheckerType.STDOUT_EXACT,
        'stdout_regex': Task.CheckerType.STDOUT_REGEX,
        'stdin_stdout': Task.CheckerType.STDIN_STDOUT,
        'custom': Task.CheckerType.CUSTOM,
        'manual': Task.CheckerType.MANUAL,
        'code': Task.CheckerType.STDIN_STDOUT,
    }
    return mapping.get(raw, Task.CheckerType.STDIN_STDOUT)


def _map_task_type(raw: str) -> str:
    mapping = {
        'practice': Task.TaskType.PRACTICE,
        'quiz': Task.TaskType.QUIZ,
        'project': Task.TaskType.PROJECT,
        'challenge': Task.TaskType.CHALLENGE,
        'code': Task.TaskType.PRACTICE,
    }
    return mapping.get(raw, Task.TaskType.PRACTICE)


def _create_task_from_data(lesson: Lesson, item: dict[str, Any], sort_order: int) -> Task:
    language_slug = item.get('language') or lesson.language.slug
    language = _get_language(language_slug)
    checker_type = _map_checker_type(item.get('checker_type', 'stdin_stdout'))
    checker_config = dict(item.get('checker_config_json') or {})
    expected_output = item.get('expected_output') or item.get('expected_stdout', '')
    if checker_type == Task.CheckerType.STDOUT_REGEX and expected_output:
        checker_config.setdefault('pattern', expected_output)
    slug = item.get('slug') or slugify(item['title'], allow_unicode=True)
    slug = _unique_slug(Task, slug, lesson=lesson)
    return Task.objects.create(
        lesson=lesson,
        language=language,
        slug=slug,
        title=item['title'],
        description=item.get('description', ''),
        task_type=_map_task_type(item.get('type', item.get('task_type', 'practice'))),
        starter_code=item.get('starter_code', ''),
        solution_template=item.get('solution_template', ''),
        stdin=item.get('stdin', ''),
        expected_stdout=expected_output if checker_type == Task.CheckerType.STDOUT_EXACT else '',
        checker_type=checker_type,
        visible_tests_json=item.get('visible_tests', item.get('visible_tests_json', [])),
        hidden_tests_json=item.get('hidden_tests', item.get('hidden_tests_json', [])),
        checker_config_json=checker_config,
        max_xp=item.get('max_xp', 5),
        difficulty=item.get('difficulty', 'easy'),
        is_required=item.get('is_required', True),
        sort_order=item.get('sort_order', sort_order),
    )


def import_course_data(data: dict[str, Any], author) -> Course:
    language = _get_language(data.get('language') or data.get('primary_language', 'python'))
    slug = data.get('slug') or slugify(data['title'], allow_unicode=True)
    slug = _unique_slug(Course, slug)

    course = Course.objects.create(
        title=data['title'],
        slug=slug,
        description=data.get('description', ''),
        primary_language=language,
        age_from=data.get('age_from'),
        age_to=data.get('age_to'),
        level=data.get('level', ''),
        author=author,
        version=data.get('version', '1.0'),
        status=data.get('status', Course.Status.DRAFT),
        cover_image=data.get('cover_image', ''),
        visibility=data.get('visibility', Course.Visibility.PUBLIC),
        settings_json=data.get('settings_json', {}),
    )

    for idx, lesson_data in enumerate(data.get('lessons', []), start=1):
        import_lesson_data(lesson_data, course=course, author=author, default_number=idx)

    return course


def import_lesson_data(
    data: dict[str, Any],
    *,
    course: Course | None = None,
    course_id: int | None = None,
    author=None,
    default_number: int = 1,
) -> Lesson:
    if course is None:
        if not course_id:
            raise ImportServiceError('Укажите course_id.')
        course = Course.objects.get(pk=course_id)

    language = _get_language(data.get('language') or course.primary_language.slug)
    slug = data.get('slug') or slugify(data['title'], allow_unicode=True)
    slug = _unique_slug(Lesson, slug, course=course)

    lesson = Lesson.objects.create(
        course=course,
        language=language,
        number=data.get('number', default_number),
        title=data['title'],
        slug=slug,
        goal=data.get('goal', ''),
        theory_text=data.get('theory', data.get('theory_text', '')),
        simple_explanation=data.get('simple_explanation', ''),
        practice_text=data.get('practice', data.get('practice_text', '')),
        mini_project_text=data.get('mini_project', data.get('mini_project_text', '')),
        summary_text=data.get('summary', data.get('summary_text', '')),
        max_xp=data.get('max_xp', data.get('xp', 0)),
        author=author,
        version=data.get('version', '1.0'),
        status=data.get('status', Lesson.Status.DRAFT),
        content_format=data.get('content_format', Lesson.ContentFormat.MARKDOWN),
        source_import_id=data.get('source_import_id', ''),
        assets_json=data.get('assets', data.get('assets_json', [])),
        sort_order=data.get('sort_order', data.get('number', default_number)),
    )

    tasks = data.get('tasks', [])
    for idx, task_data in enumerate(tasks, start=1):
        _create_task_from_data(lesson, task_data, idx)

    return lesson


def parse_markdown_lesson(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    title = ''
    current_section = None
    sections: dict[str, list[str]] = {}

    for line in lines:
        if line.startswith('# ') and not title:
            title = line[2:].strip()
            continue
        if line.startswith('## '):
            current_section = line[3:].strip().lower()
            sections[current_section] = []
            continue
        if current_section is not None:
            sections[current_section].append(line)

    def section_text(*names: str) -> str:
        for name in names:
            key = name.lower()
            if key in sections:
                return '\n'.join(sections[key]).strip()
        return ''

    return {
        'title': title or 'Imported lesson',
        'goal': section_text('цель', 'goal'),
        'theory': section_text('теория', 'theory'),
        'simple_explanation': section_text('простое объяснение', 'simple explanation'),
        'practice': section_text('практика', 'practice'),
        'mini_project': section_text('мини-проект', 'mini-project', 'mini project'),
        'summary': section_text('вопросы', 'summary'),
        'max_xp': _parse_xp(section_text('xp')),
    }


def _parse_xp(text: str) -> int:
    match = re.search(r'\d+', text or '')
    return int(match.group()) if match else 0


def import_lesson_markdown(text: str, **kwargs) -> Lesson:
    data = parse_markdown_lesson(text)
    return import_lesson_data(data, **kwargs)


def import_tasks_data(data: dict[str, Any] | list, lesson_id: int) -> list[Task]:
    lesson = Lesson.objects.select_related('course', 'language').get(pk=lesson_id)
    items = data if isinstance(data, list) else data.get('tasks', [])
    if not items:
        raise ImportServiceError('Список заданий пуст.')
    created = []
    for idx, item in enumerate(items, start=1):
        created.append(_create_task_from_data(lesson, item, idx))
    return created


def import_course_zip(file_obj, author) -> Course:
    with zipfile.ZipFile(file_obj) as zf:
        if 'course.json' not in zf.namelist():
            raise ImportServiceError('ZIP должен содержать course.json')
        course_data = json.loads(zf.read('course.json').decode('utf-8'))
        course = import_course_data(course_data, author)

        for name in zf.namelist():
            if name.startswith('lessons/') and name.endswith('.md'):
                lesson_data = parse_markdown_lesson(zf.read(name).decode('utf-8'))
                import_lesson_data(lesson_data, course=course, author=author)
            elif name.startswith('tasks/') and name.endswith('.json'):
                tasks_data = json.loads(zf.read(name).decode('utf-8'))
                lesson_slug = name.replace('tasks/', '').replace('_tasks.json', '').replace('.json', '')
                lesson = Lesson.objects.filter(course=course, slug__icontains=lesson_slug).first()
                if lesson:
                    import_tasks_data(tasks_data, lesson.id)
        return course


def export_course(course_id: int) -> dict[str, Any]:
    course = Course.objects.select_related('primary_language').get(pk=course_id)
    lessons = Lesson.objects.filter(course=course).prefetch_related('tasks')
    return {
        'title': course.title,
        'slug': course.slug,
        'description': course.description,
        'language': course.primary_language.slug,
        'age_from': course.age_from,
        'age_to': course.age_to,
        'level': course.level,
        'version': course.version,
        'status': course.status,
        'visibility': course.visibility,
        'settings_json': course.settings_json,
        'lessons': [
            {
                'number': lesson.number,
                'title': lesson.title,
                'slug': lesson.slug,
                'language': lesson.language.slug,
                'goal': lesson.goal,
                'theory': lesson.theory_text,
                'simple_explanation': lesson.simple_explanation,
                'practice': lesson.practice_text,
                'mini_project': lesson.mini_project_text,
                'summary': lesson.summary_text,
                'max_xp': lesson.max_xp,
                'status': lesson.status,
                'sort_order': lesson.sort_order,
                'tasks': [
                    {
                        'title': task.title,
                        'description': task.description,
                        'type': task.task_type,
                        'language': task.language.slug,
                        'starter_code': task.starter_code,
                        'checker_type': task.checker_type,
                        'stdin': task.stdin,
                        'expected_stdout': task.expected_stdout,
                        'visible_tests': task.visible_tests_json,
                        'hidden_tests': task.hidden_tests_json,
                        'checker_config_json': task.checker_config_json,
                        'max_xp': task.max_xp,
                        'difficulty': task.difficulty,
                        'is_required': task.is_required,
                        'sort_order': task.sort_order,
                    }
                    for task in lesson.tasks.all()
                ],
            }
            for lesson in lessons
        ],
    }


def export_leaderboard(course_id=None, group_id=None) -> dict[str, Any]:
    from apps.gamification.services import get_leaderboard

    entries = get_leaderboard(
        course_id=int(course_id) if course_id else None,
        group_id=int(group_id) if group_id else None,
        limit=1000,
    )
    return {
        'course_id': course_id,
        'group_id': group_id,
        'entries': entries,
        'exported_at': timezone.now().isoformat(),
    }


def run_import_job(job: ImportJob, payload: dict[str, Any]) -> ImportJob:
    job.status = ImportJob.Status.PROCESSING
    job.save(update_fields=['status'])
    try:
        with transaction.atomic():
            if job.import_type == ImportJob.ImportType.COURSE:
                if payload.get('zip_bytes'):
                    course = import_course_zip(BytesIO(payload['zip_bytes']), job.user)
                else:
                    course = import_course_data(payload['data'], job.user)
                job.result_json = {'course_id': course.id, 'slug': course.slug}
            elif job.import_type == ImportJob.ImportType.LESSON:
                if payload.get('markdown'):
                    lesson = import_lesson_markdown(
                        payload['markdown'],
                        course_id=payload.get('course_id'),
                        author=job.user,
                    )
                else:
                    lesson = import_lesson_data(
                        payload['data'],
                        course_id=payload.get('course_id'),
                        author=job.user,
                    )
                job.result_json = {'lesson_id': lesson.id, 'slug': lesson.slug}
            elif job.import_type == ImportJob.ImportType.TASKS:
                tasks = import_tasks_data(payload['data'], payload['lesson_id'])
                job.result_json = {'task_ids': [t.id for t in tasks], 'count': len(tasks)}
            else:
                raise ImportServiceError(f'Неизвестный тип импорта: {job.import_type}')
        job.status = ImportJob.Status.COMPLETED
        job.errors_json = []
    except Exception as exc:
        job.status = ImportJob.Status.FAILED
        job.errors_json = [str(exc)]
        job.result_json = {}
    job.finished_at = timezone.now()
    job.save()
    return job
