import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed platform with initial admin, demo student, languages, and optional JSON data.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CodeLearn platform...')

        admin_user, created = User.objects.get_or_create(
            username=settings.INITIAL_ADMIN_USERNAME,
            defaults={
                'email': settings.INITIAL_ADMIN_EMAIL,
                'display_name': 'Administrator',
                'role': User.Role.SUPERADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin_user.set_password(settings.INITIAL_ADMIN_PASSWORD)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin: {admin_user.username}'))
        else:
            self.stdout.write(f'Admin already exists: {admin_user.username}')

        if settings.CREATE_DEMO_STUDENT:
            student, created = User.objects.get_or_create(
                username=settings.DEMO_STUDENT_USERNAME,
                defaults={
                    'email': f'{settings.DEMO_STUDENT_USERNAME}@localhost',
                    'display_name': settings.DEMO_STUDENT_NAME,
                    'role': User.Role.STUDENT,
                },
            )
            if created:
                student.set_password(settings.DEMO_STUDENT_PASSWORD)
                student.save()
                self.stdout.write(self.style.SUCCESS(f'Created demo student: {student.username}'))

        self._seed_default_languages()
        self._load_seed_json()
        course = self._seed_python_course(admin_user)
        if settings.CREATE_DEMO_STUDENT:
            student = User.objects.filter(username=settings.DEMO_STUDENT_USERNAME).first()
            if student and course:
                self._assign_course_to_student(student, course, admin_user)
                self._seed_demo_parent(student)
        self._seed_badges()
        self.stdout.write(self.style.SUCCESS('Seed complete.'))

    def _seed_demo_parent(self, student):
        parent, created = User.objects.get_or_create(
            username='parent',
            defaults={
                'email': 'parent@localhost',
                'display_name': 'Родитель (демо)',
                'role': User.Role.PARENT,
            },
        )
        if created:
            parent.set_password('parent123')
            parent.save()
            self.stdout.write(self.style.SUCCESS('Created demo parent: parent / parent123'))
        parent.children.add(student)

    def _seed_python_course(self, author):
        from apps.courses.models import Course
        from apps.imports.services import import_course_data

        course_file = settings.SEED_DATA_DIR / 'python_starter_course.json'
        if not course_file.exists():
            self.stdout.write(f'No course seed at {course_file}')
            return None

        existing = Course.objects.filter(slug='python-starter').first()
        if existing:
            self.stdout.write(f'Course already exists: {existing.title}')
            return existing

        data = json.loads(course_file.read_text(encoding='utf-8'))
        course = import_course_data(data, author=author)
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=['status'])
        self.stdout.write(self.style.SUCCESS(f'Created course: {course.title} ({course.lessons.count()} lessons)'))
        return course

    def _assign_course_to_student(self, student, course, admin):
        from apps.accounts.models import Group, GroupUser
        from apps.courses.models import CourseAssignment

        group, _ = Group.objects.get_or_create(
            title='Стартовая группа',
            defaults={'description': 'Демо-группа для стартового курса', 'teacher': admin},
        )
        GroupUser.objects.get_or_create(group=group, user=student)
        CourseAssignment.objects.get_or_create(
            course=course,
            user=student,
            defaults={'assigned_by': admin, 'status': CourseAssignment.Status.ACTIVE},
        )
        CourseAssignment.objects.get_or_create(
            course=course,
            group=group,
            defaults={'assigned_by': admin, 'status': CourseAssignment.Status.ACTIVE},
        )
        self.stdout.write(self.style.SUCCESS(f'Assigned course to {student.username}'))

    def _seed_badges(self):
        from apps.courses.models import Course
        from apps.gamification.models import Badge

        course = Course.objects.filter(slug='python-starter').first()
        badges = [
            {'title': 'Первый урок', 'description': 'Выполнен первый урок', 'badge_type': Badge.BadgeType.ACHIEVEMENT, 'condition_type': Badge.ConditionType.LESSONS_COMPLETED, 'condition_value': 1},
            {'title': 'Python-старт', 'description': 'Начал курс Python', 'badge_type': Badge.BadgeType.COURSE, 'condition_type': Badge.ConditionType.MANUAL, 'condition_value': None, 'course': course},
            {'title': '10 уроков', 'description': 'Выполнено 10 уроков', 'badge_type': Badge.BadgeType.ACHIEVEMENT, 'condition_type': Badge.ConditionType.LESSONS_COMPLETED, 'condition_value': 10},
        ]
        for item in badges:
            title = item.pop('title')
            Badge.objects.get_or_create(title=title, defaults=item)

    def _seed_default_languages(self):
        from apps.courses.models import ProgrammingLanguage

        defaults = [
            {
                'name': 'Python',
                'slug': 'python',
                'judge0_language_id': 71,
                'version': '3.12',
                'editor_mode': 'python',
                'starter_code': '# Напиши код здесь\n',
            },
            {
                'name': 'JavaScript',
                'slug': 'javascript',
                'judge0_language_id': 63,
                'version': 'ES2020',
                'editor_mode': 'javascript',
                'starter_code': '// Напиши код здесь\n',
            },
            {
                'name': 'Java',
                'slug': 'java',
                'judge0_language_id': 62,
                'version': '17',
                'editor_mode': 'java',
                'starter_code': 'public class Main {\n    public static void main(String[] args) {\n        \n    }\n}\n',
            },
        ]
        for item in defaults:
            _, created = ProgrammingLanguage.objects.update_or_create(slug=item['slug'], defaults=item)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created language: {item["slug"]}'))

    def _load_seed_json(self):
        seed_dir = Path(settings.SEED_DATA_DIR)
        if not seed_dir.exists():
            self.stdout.write(f'No seed data directory at {seed_dir}; skipping JSON seed.')
            return

        from apps.courses.models import ProgrammingLanguage

        languages_file = seed_dir / 'languages.json'
        if languages_file.exists():
            data = json.loads(languages_file.read_text(encoding='utf-8'))
            for item in data:
                ProgrammingLanguage.objects.update_or_create(slug=item['slug'], defaults=item)
            self.stdout.write(f'Loaded languages from {languages_file.name}')

        courses_file = seed_dir / 'courses.json'
        if courses_file.exists():
            self.stdout.write(f'Found {courses_file.name} — use python_starter_course.json via _seed_python_course.')
