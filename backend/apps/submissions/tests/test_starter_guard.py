from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from apps.submissions.starter_guard import (
    is_unchanged_starter,
    normalize_student_code,
    should_reject_unchanged_starter,
)

User = get_user_model()


class NormalizeStudentCodeTests(SimpleTestCase):
    def test_strips_comments_blanks_and_trailing_space(self):
        raw = 'a = 1  \n\n# comment\nb = 2\n'
        self.assertEqual(normalize_student_code(raw), 'a=1\nb=2')

    def test_empty_after_comments_is_empty(self):
        self.assertEqual(normalize_student_code('# only\n\n'), '')


class UnchangedStarterTests(SimpleTestCase):
    def test_identical_code(self):
        starter = 'print("hi")\n'
        self.assertTrue(is_unchanged_starter(starter, starter))

    def test_comment_only_change_still_unchanged(self):
        starter = 'n = int(input())\nprint(n)\n'
        submitted = 'n = int(input())\n# Измени код\nprint(n)\n'
        self.assertTrue(is_unchanged_starter(submitted, starter))

    def test_real_change_is_detected(self):
        starter = 'n = int(input())\n'
        submitted = 'n = int(input())\nif n > 0:\n    print("ok")\n'
        self.assertFalse(is_unchanged_starter(submitted, starter))

    def test_personalize_token(self):
        user = User(username='gosha', display_name='Гоша')
        starter = 'name = "{{ student_name }}"\nprint(name)\n'
        submitted = 'name = "Гоша"\nprint(name)\n'
        self.assertTrue(is_unchanged_starter(submitted, starter, user))

    def test_run_only_not_rejected(self):
        class Task:
            title = 'Запусти пример'
            starter_code = 'print(1)\n'

        self.assertFalse(should_reject_unchanged_starter(Task(), 'print(1)\n'))

    def test_graded_unchanged_rejected(self):
        class Task:
            title = 'Задание урока 6'
            starter_code = 'n = int(input())\n'

        self.assertTrue(should_reject_unchanged_starter(Task(), 'n = int(input())\n# x\n'))
