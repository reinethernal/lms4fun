import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.courses.models import Course
from apps.lessons.models import Lesson


class Command(BaseCommand):
    help = 'Sync lesson theory content from python_starter_course.json into the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-slug',
            default='python-starter',
            help='Course slug to update (default: python-starter)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show changes without saving',
        )

    def handle(self, *args, **options):
        course_slug = options['course_slug']
        dry_run = options['dry_run']

        seed_path = Path(settings.SEED_DATA_DIR) / 'python_starter_course.json'
        if not seed_path.exists():
            self.stderr.write(self.style.ERROR(f'Seed file not found: {seed_path}'))
            return

        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Course not found: {course_slug}'))
            return

        data = json.loads(seed_path.read_text(encoding='utf-8'))
        lessons_data = data.get('lessons', [])
        updated = 0
        missing = []

        for item in lessons_data:
            slug = item.get('slug')
            if not slug:
                continue
            lesson = Lesson.objects.filter(course=course, slug=slug).first()
            if lesson is None:
                missing.append(slug)
                continue

            fields = {
                'goal': item.get('goal', lesson.goal),
                'theory_text': item.get('theory', item.get('theory_text', lesson.theory_text)),
                'simple_explanation': item.get('simple_explanation', lesson.simple_explanation),
                'practice_text': item.get('practice', item.get('practice_text', lesson.practice_text)),
                'mini_project_text': item.get('mini_project', item.get('mini_project_text', lesson.mini_project_text)),
                'summary_text': item.get('summary', item.get('summary_text', lesson.summary_text)),
            }

            if dry_run:
                self.stdout.write(f'Would update lesson {slug}: {lesson.title}')
            else:
                for attr, value in fields.items():
                    setattr(lesson, attr, value or '')
                lesson.save(update_fields=list(fields.keys()))
                updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f'Dry run: {len(lessons_data) - len(missing)} lessons would be updated'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} lessons for course "{course_slug}"'))

        if missing:
            self.stdout.write(self.style.WARNING(f'Missing in DB: {", ".join(missing)}'))
