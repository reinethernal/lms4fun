from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.courses.models import Course, ProgrammingLanguage
from apps.lessons.models import Lesson
from apps.submissions.checker import check_stdout_exact, evaluate_submission
from apps.tasks.models import Task

User = get_user_model()


class CheckerStdoutExactTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_checker',
            password='test',
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.language = ProgrammingLanguage.objects.create(
            name='Python',
            slug='python-checker',
            judge0_language_id=71,
        )
        self.course = Course.objects.create(
            title='Course',
            slug='course-checker',
            author=self.admin,
            primary_language=self.language,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            number=1,
            title='Lesson 1',
            slug='lesson-checker',
            language=self.language,
            status=Lesson.Status.PUBLISHED,
        )
        self.task = Task.objects.create(
            lesson=self.lesson,
            language=self.language,
            title='Hello task',
            sort_order=1,
            checker_type=Task.CheckerType.STDOUT_EXACT,
            stdin='Administrator',
            expected_stdout='Привет! Я Administrator!',
            starter_code='name = input("Как тебя зовут? ")\nprint(f"Привет! Я {name}!")',
        )

    def test_check_stdout_exact_strips_input_prompts(self):
        source = 'name = input("Как тебя зовут? ")\nprint(f"Привет! Я {name}!")'
        actual = 'Как тебя зовут? Привет! Я Administrator!!!!'
        passed, _msg = check_stdout_exact(actual, 'Привет! Я Administrator!', source)
        self.assertFalse(passed)

    def test_evaluate_rejects_unchanged_starter(self):
        result = evaluate_submission(self.task, self.task.starter_code, user=self.admin)
        self.assertFalse(result['accepted'])
        self.assertTrue(result.get('unchanged_starter'))
        self.assertIn('измени код', result['message'].lower())

    def test_evaluate_rejects_comment_only_change(self):
        code = self.task.starter_code.rstrip() + '\n# cosmetic\n'
        result = evaluate_submission(self.task, code, user=self.admin)
        self.assertFalse(result['accepted'])
        self.assertTrue(result.get('unchanged_starter'))

    @patch('apps.submissions.checker.Judge0Client')
    def test_evaluate_submission_stdout_exact_fail_includes_expected_got(self, client_cls):
        client = MagicMock()
        client_cls.return_value = client
        client.run_code.return_value = {
            'stdout': 'Как тебя зовут? Привет! Я Administrator!!!!',
            'stderr': '',
            'compile_output': '',
            'status': {'id': 3, 'description': 'Accepted'},
            'time': '0.01',
            'memory': 1000,
        }

        source = 'name = input("Как тебя зовут? ")\nprint(f"Привет! Я {name}!!!!")'
        result = evaluate_submission(self.task, source)

        self.assertFalse(result['accepted'])
        self.assertEqual(result['status'], 'wrong_answer')
        self.assertIn('Ожидалось', result['message'])
        self.assertEqual(result['expected'], 'Привет! Я Administrator!')
        self.assertEqual(result['got'], 'Привет! Я Administrator!!!!')
        self.assertFalse(result['is_hidden'])

    @patch('apps.submissions.checker.Judge0Client')
    def test_failure_feedback_uses_submission_source_code(self, client_cls):
        self.task.checker_type = Task.CheckerType.STDIN_STDOUT
        self.task.visible_tests_json = [
            {'stdin': 'Administrator', 'expected_stdout': 'Привет! Я Administrator!'},
        ]
        self.task.stdin = ''
        self.task.expected_stdout = ''
        self.task.save(update_fields=[
            'checker_type', 'visible_tests_json', 'stdin', 'expected_stdout',
        ])

        client = MagicMock()
        client_cls.return_value = client
        client.run_code.return_value = {
            'stdout': 'Как тебя зовут? Привет! Я Administrator!!!!',
            'stderr': '',
            'compile_output': '',
            'status': {'id': 3, 'description': 'Accepted'},
            'time': '0.01',
            'memory': 1000,
        }

        source = 'name = input("Как тебя зовут? ")\nprint(f"Привет! Я {name}!!!!")'
        result = evaluate_submission(self.task, source)

        self.assertFalse(result['accepted'])
        self.assertEqual(result['got'], 'Привет! Я Administrator!!!!')
        self.assertFalse(result['is_hidden'])
