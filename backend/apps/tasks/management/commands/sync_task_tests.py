import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.courses.models import Course, ProgrammingLanguage
from apps.lessons.models import Lesson
from apps.tasks.models import Task


class Command(BaseCommand):
    help = 'Sync task checker config and tests from python_starter_course.json'

    def add_arguments(self, parser):
        parser.add_argument('--course-slug', default='python-starter')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--create-missing', action='store_true', default=True)
        parser.add_argument('--no-create-missing', action='store_false', dest='create_missing')

    def handle(self, *args, **options):
        course_slug = options['course_slug']
        dry_run = options['dry_run']
        create_missing = options['create_missing']
        seed_path = Path(settings.SEED_DATA_DIR) / 'python_starter_course.json'
        data = json.loads(seed_path.read_text(encoding='utf-8'))
        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Course not found: {course_slug}'))
            return

        language = course.primary_language or ProgrammingLanguage.objects.filter(slug='python').first()
        if language is None:
            self.stderr.write(self.style.ERROR('No programming language found'))
            return

        # Avoid unique_together collisions when matching by sort_order while slug differs
        updated = 0
        created = 0
        missing = []
        for lesson_data in data.get('lessons', []):
            lesson_slug = lesson_data.get('slug')
            lesson = course.lessons.filter(slug=lesson_slug).first()
            if not lesson:
                continue
            practice = lesson_data.get('practice')
            mini_project = lesson_data.get('mini_project')
            if practice is not None or mini_project is not None:
                if dry_run:
                    self.stdout.write(f'Would update lesson content {lesson_slug}')
                else:
                    fields = []
                    if practice is not None:
                        lesson.practice_text = practice
                        fields.append('practice_text')
                    if mini_project is not None:
                        lesson.mini_project_text = mini_project
                        fields.append('mini_project_text')
                    if fields:
                        lesson.save(update_fields=fields)

            for task_data in lesson_data.get('tasks', []):
                qs = Task.objects.filter(lesson=lesson)
                task = None
                if task_data.get('slug'):
                    task = qs.filter(slug=task_data['slug']).first()
                if task is None and task_data.get('title'):
                    # Prefer title match before sort_order so new tasks don't overwrite wrong rows
                    task = qs.filter(title=task_data['title']).first()
                if task is None and task_data.get('sort_order') is not None and not task_data.get('slug'):
                    task = qs.filter(sort_order=task_data.get('sort_order', 0)).first()

                expected_output = task_data.get('expected_stdout', task_data.get('expected_output', ''))
                checker_type = task_data.get('checker_type', Task.CheckerType.STDOUT_EXACT)
                checker_config = dict(task_data.get('checker_config_json') or {})
                if checker_type == Task.CheckerType.STDOUT_REGEX and expected_output:
                    checker_config.setdefault('pattern', expected_output)

                fields = {
                    'title': task_data.get('title', ''),
                    'description': task_data.get('description', ''),
                    'task_type': task_data.get('type', Task.TaskType.PRACTICE),
                    'starter_code': task_data.get('starter_code', ''),
                    'checker_type': checker_type,
                    'stdin': task_data.get('stdin', ''),
                    'expected_stdout': expected_output if checker_type != Task.CheckerType.STDOUT_REGEX else (
                        checker_config.get('pattern', expected_output)
                    ),
                    'visible_tests_json': task_data.get('visible_tests_json', []),
                    'hidden_tests_json': task_data.get('hidden_tests_json', []),
                    'checker_config_json': checker_config,
                    'max_xp': task_data.get('max_xp', 5),
                    'is_required': task_data.get('is_required', True),
                    'sort_order': task_data.get('sort_order', 0),
                }
                if task_data.get('slug'):
                    fields['slug'] = task_data['slug']

                if task is None:
                    if not create_missing:
                        missing.append(f'{lesson_slug}/{task_data.get("title")}')
                        continue
                    if dry_run:
                        self.stdout.write(f'Would create task {lesson_slug}/{task_data.get("title")}')
                        created += 1
                        continue
                    task = Task.objects.create(lesson=lesson, language=language, **fields)
                    created += 1
                    continue

                if dry_run:
                    self.stdout.write(f'Would update task {task.id} {task.title}')
                else:
                    for attr, val in fields.items():
                        setattr(task, attr, val)
                    task.save(update_fields=list(fields.keys()))
                    updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run complete'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} tasks, created {created}'))
        if missing:
            self.stdout.write(self.style.WARNING('Missing: ' + ', '.join(missing[:10])))
