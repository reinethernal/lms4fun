"""Audit that required-task starters cannot be submitted / auto-accepted unchanged."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.courses.models import Course
from apps.submissions.checker import evaluate_submission
from apps.submissions.error_explainer import explain_stdin_validation
from apps.submissions.starter_guard import is_unchanged_starter, should_reject_unchanged_starter
from apps.tasks.demo import is_run_only_task
from apps.tasks.personalize import personalize_text

User = get_user_model()

# Lessons that previously used trivial `.+` — print(1) must not pass.
TRIVIAL_PRINT_LESSONS = {2, 3, 11, 12, 15, 18, 23}

REFERENCE_SOLUTIONS = {
    2: 'name = "{{ student_name }}"\nprint(name)\n',
    3: 'name = "{{ student_name }}"\nprint(f"Меня зовут {name}")\n',
    6: 'n = int(input())\nif n > 0:\n    print("положительное")\nelse:\n    print("не положительное")\n',
    7: (
        'x = int(input())\n'
        'if x > 10:\n    print("большое")\n'
        'elif x > 0:\n    print("маленькое")\n'
        'else:\n    print("отрицательное")\n'
    ),
    8: 'import random\nprint(random.randint(1, 10))\n',
    9: 'i = 1\nwhile i <= 3:\n    print(i)\n    i += 1\n',
    10: (
        'secret = 7\n'
        'guess = int(input())\n'
        'if guess == secret:\n    print("Верно!")\n'
        'elif guess < secret:\n    print("Больше")\n'
        'else:\n    print("Меньше")\n'
    ),
    11: 'items = ["яблоко", "банан"]\nprint(items[0])\n',
    12: 'items = []\nitems.append("кот")\nprint("кот" in items)\n',
    13: 'for i in range(3):\n    print(i)\n',
    15: 'def greet(name):\n    print(f"Привет, {name}!")\ngreet("{{ student_name }}")\n',
    16: 'def add(a, b):\n    return a + b\nprint(add(2, 3))\n',
    18: 'name = "{{ student_name }}"\nprint(name)\n',
    23: 'print("Финальная игра {{ student_name }}")\n',
}


class Command(BaseCommand):
    help = 'Bugtest course starters: guard + constructs + weak-regex bypass + references'

    def add_arguments(self, parser):
        parser.add_argument('--course-slug', default='python-starter')
        parser.add_argument('--skip-judge0', action='store_true', help='Only run local guard/input checks')
        parser.add_argument(
            '--lessons-only',
            type=str,
            default='',
            help='Comma-separated lesson numbers for Judge0 reference eval (default: all refs)',
        )

    def handle(self, *args, **options):
        course_slug = options['course_slug']
        skip_judge0 = options['skip_judge0']
        lessons_only = set()
        if options['lessons_only'].strip():
            lessons_only = {int(x.strip()) for x in options['lessons_only'].split(',') if x.strip()}
        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Course not found: {course_slug}'))
            return

        user = User.objects.filter(role=User.Role.STUDENT).first()
        if user is None:
            user = User(username='audit_student', display_name='Аудит', role=User.Role.STUDENT)

        failures: list[str] = []
        checked = 0

        for lesson in course.lessons.prefetch_related('tasks').order_by('number'):
            for task in lesson.tasks.all():
                if is_run_only_task(task) or not task.is_required:
                    continue
                checked += 1
                starter = personalize_text(task.starter_code or '', user)

                if not is_unchanged_starter(starter, task.starter_code, user):
                    failures.append(f'L{lesson.number} {task.title}: personalized starter != guard baseline')
                if not should_reject_unchanged_starter(task, starter, user):
                    failures.append(f'L{lesson.number} {task.title}: guard did not reject starter')

                cosmetic = starter.rstrip() + '\n# Измени код\n'
                if not should_reject_unchanged_starter(task, cosmetic, user):
                    failures.append(f'L{lesson.number} {task.title}: comment-only change bypassed guard')

                spaced = starter.replace(' = ', '=', 1) if ' = ' in starter else starter
                if spaced != starter and not should_reject_unchanged_starter(task, spaced, user):
                    failures.append(f'L{lesson.number} {task.title}: spacing change bypassed guard')

                if 'input(' in (task.starter_code or '') or 'input(' in starter:
                    guidance = explain_stdin_validation(starter, '')
                    if guidance is None:
                        failures.append(f'L{lesson.number} {task.title}: missing stdin validation for empty stdin')

                result = evaluate_submission(task, starter, user=user)
                if result.get('accepted'):
                    failures.append(
                        f'L{lesson.number} {task.title}: unchanged starter was ACCEPTED by checker'
                    )

                if lesson.number in TRIVIAL_PRINT_LESSONS and not skip_judge0:
                    if lessons_only and lesson.number not in lessons_only:
                        pass
                    else:
                        junk = 'print(1)\n'
                        junk_result = evaluate_submission(task, junk, user=user)
                        if junk_result.get('accepted'):
                            failures.append(
                                f'L{lesson.number} {task.title}: print(1) was ACCEPTED (weak checker)'
                            )

        if not skip_judge0:
            for lesson in course.lessons.prefetch_related('tasks').filter(number__in=REFERENCE_SOLUTIONS):
                if lessons_only and lesson.number not in lessons_only:
                    continue
                task = next(
                    (t for t in lesson.tasks.all() if not is_run_only_task(t) and t.is_required),
                    None,
                )
                if task is None:
                    failures.append(f'L{lesson.number}: graded task not found')
                    continue
                code = personalize_text(REFERENCE_SOLUTIONS[lesson.number], user)
                if should_reject_unchanged_starter(task, code, user):
                    failures.append(f'L{lesson.number}: reference wrongly blocked as starter')
                    continue
                try:
                    result = evaluate_submission(task, code, user=user)
                except Exception as exc:  # noqa: BLE001
                    failures.append(f'L{lesson.number}: evaluate(reference) error: {exc}')
                    continue
                if not result.get('accepted'):
                    failures.append(
                        f'L{lesson.number}: reference NOT accepted: {result.get("message")}'
                    )

        self.stdout.write(f'Checked {checked} required tasks')
        if failures:
            for item in failures:
                self.stderr.write(self.style.ERROR(item))
            self.stderr.write(self.style.ERROR(f'{len(failures)} failure(s)'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('Bugtest passed'))
