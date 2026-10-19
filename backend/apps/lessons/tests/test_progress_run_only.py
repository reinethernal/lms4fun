from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.courses.models import Course, ProgrammingLanguage
from apps.lessons.models import Lesson
from apps.lessons.progress import is_lesson_completed
from apps.tasks.models import Task

User = get_user_model()


class LessonProgressRunOnlyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='progress_test',
            password='test',
            role=User.Role.STUDENT,
        )
        self.language = ProgrammingLanguage.objects.create(
            name='Python',
            slug='python-test',
            judge0_language_id=71,
        )
        self.course = Course.objects.create(
            title='Test',
            slug='test-course-progress',
            author=self.user,
            primary_language=self.language,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            number=1,
            title='Lesson',
            slug='lesson-progress-test',
            language=self.language,
        )
        self.demo_task = Task.objects.create(
            lesson=self.lesson,
            language=self.language,
            title='Запусти пример',
            is_required=True,
            sort_order=1,
        )
        self.practice_task = Task.objects.create(
            lesson=self.lesson,
            language=self.language,
            title='Моя программа',
            is_required=True,
            sort_order=2,
        )

    def test_demo_task_not_required_for_completion(self):
        self.assertFalse(is_lesson_completed(self.user, self.lesson))

        from apps.submissions.models import Submission

        Submission.objects.create(
            user=self.user,
            task=self.practice_task,
            language=self.language,
            code='print("hi")',
            status=Submission.Status.ACCEPTED,
        )
        self.assertTrue(is_lesson_completed(self.user, self.lesson))

    def test_demo_only_lesson_completes_without_submissions(self):
        Task.objects.filter(id=self.practice_task.id).delete()
        self.assertTrue(is_lesson_completed(self.user, self.lesson))
