from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Group, GroupUser
from apps.courses.models import Course, ProgrammingLanguage
from apps.lessons.models import Lesson
from apps.submissions.models import Submission
from apps.tasks.models import Task

User = get_user_model()


class SubmissionHistoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin_hist',
            password='test',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.teacher = User.objects.create_user(
            username='teacher_hist',
            password='test',
            role=User.Role.TEACHER,
            is_staff=True,
        )
        self.other_teacher = User.objects.create_user(
            username='teacher_other',
            password='test',
            role=User.Role.TEACHER,
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student_hist',
            password='test',
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username='student_other',
            password='test',
            role=User.Role.STUDENT,
        )
        self.language = ProgrammingLanguage.objects.create(
            name='Python',
            slug='python-hist',
            judge0_language_id=71,
        )
        self.course = Course.objects.create(
            title='Course',
            slug='course-hist',
            author=self.admin,
            primary_language=self.language,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            number=1,
            title='Lesson 1',
            slug='lesson-hist',
            language=self.language,
            status=Lesson.Status.PUBLISHED,
        )
        self.task = Task.objects.create(
            lesson=self.lesson,
            language=self.language,
            title='Task A',
            sort_order=1,
        )
        group = Group.objects.create(title='G1', teacher=self.teacher)
        GroupUser.objects.create(group=group, user=self.student)

        self.sub1 = Submission.objects.create(
            user=self.student,
            task=self.task,
            language=self.language,
            code='print(1)',
            status=Submission.Status.REJECTED,
        )
        self.sub2 = Submission.objects.create(
            user=self.student,
            task=self.task,
            language=self.language,
            code='print(2)',
            status=Submission.Status.ACCEPTED,
            xp_awarded=5,
        )

    def test_student_submissions_list_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/students/{self.student.id}/submissions')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_student_submissions_filter_by_task(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            f'/api/students/{self.student.id}/submissions',
            {'task_id': self.task.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['task']['lesson_title'], 'Lesson 1')

    def test_teacher_can_view_own_student_submissions(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(f'/api/students/{self.student.id}/submissions')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_view_other_student_submissions(self):
        self.client.force_authenticate(user=self.other_teacher)
        response = self.client.get(f'/api/students/{self.student.id}/submissions')
        self.assertEqual(response.status_code, 403)

    def test_admin_submissions_task_id_filter(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            '/api/admin/submissions',
            {'user_id': self.student.id, 'task_id': self.task.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_teacher_admin_submissions_scoped_to_group(self):
        Submission.objects.create(
            user=self.other_student,
            task=self.task,
            language=self.language,
            code='print(3)',
            status=Submission.Status.ACCEPTED,
        )
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/admin/submissions')
        self.assertEqual(response.status_code, 200)
        user_ids = {item['user']['id'] for item in response.data}
        self.assertIn(self.student.id, user_ids)
        self.assertNotIn(self.other_student.id, user_ids)
