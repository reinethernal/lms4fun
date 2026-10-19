from django.test import SimpleTestCase

from apps.submissions.construct_guard import check_required_constructs
from apps.submissions.starter_guard import is_unchanged_starter, normalize_student_code


class NormalizeSpacingTests(SimpleTestCase):
    def test_spaces_around_equals_are_ignored(self):
        self.assertEqual(
            normalize_student_code('name = "Гоша"'),
            normalize_student_code('name="Гоша"'),
        )

    def test_whitespace_only_change_matches_starter(self):
        starter = 'n = int(input())\n'
        submitted = 'n=int(input())\n'
        self.assertTrue(is_unchanged_starter(submitted, starter))


class ConstructGuardTests(SimpleTestCase):
    def test_required_constructs_missing(self):
        msg = check_required_constructs('print(5)', {'required_constructs': ['while']})
        self.assertIsNotNone(msg)
        self.assertIn('while', msg)

    def test_required_constructs_present(self):
        self.assertIsNone(
            check_required_constructs(
                'i=1\nwhile i<=3:\n    print(i)\n    i+=1\n',
                {'required_constructs': ['while']},
            )
        )

    def test_required_any(self):
        self.assertIsNone(
            check_required_constructs('for i in range(3):\n    print(i)\n', {
                'required_any': [['for', 'range']],
            })
        )
        self.assertIsNotNone(
            check_required_constructs('print(0)\nprint(1)\nprint(2)\n', {
                'required_any': [['for', 'range']],
            })
        )

    def test_comments_do_not_satisfy_construct(self):
        msg = check_required_constructs('# while\nprint(1)\n', {'required_constructs': ['while']})
        self.assertIsNotNone(msg)
