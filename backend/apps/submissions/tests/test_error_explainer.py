from django.test import SimpleTestCase

from apps.submissions.error_explainer import (
    explain_execution_error,
    guidance_summary,
    is_waiting_for_input,
)


EOF_TRACEBACK = '''Traceback (most recent call last):
  File "/box/script.py", line 1, in <module>
    student_name = input("Как тебя зовут?")
                   ^^^^^^^^^^^^^^^^^^^^^^^^
EOFError: EOF when reading a line'''

SYNTAX_TRACEBACK = '''  File "/box/script.py", line 2
    if x > 0
            ^
SyntaxError: invalid syntax'''

NAME_TRACEBACK = '''Traceback (most recent call last):
  File "/box/script.py", line 3, in <module>
    print(score)
          ^^^^^
NameError: name 'score' is not defined'''

VALUE_TRACEBACK = '''Traceback (most recent call last):
  File "/box/script.py", line 2, in <module>
    print(int("abc"))
          ^^^^^^^^^^
ValueError: invalid literal for int() with base 10: 'abc'''


class ErrorExplainerTests(SimpleTestCase):
    def test_explain_python_errors(self):
        cases = [
            (EOF_TRACEBACK, 'name = input()\nprint(name)', '', True, 'eof_error'),
            (EOF_TRACEBACK, 'a = input()\nb = input()', 'один', True, 'eof_error'),
            (SYNTAX_TRACEBACK, 'if x > 0\n    pass', '', True, 'syntax_error'),
            (NAME_TRACEBACK, 'print(score)', '', True, 'name_error'),
            (VALUE_TRACEBACK, 'print(int("abc"))', '', True, 'value_error'),
        ]
        for stderr, source_code, stdin, is_trial_run, expected_type in cases:
            with self.subTest(expected_type=expected_type):
                guidance = explain_execution_error(
                    stderr,
                    source_code=source_code,
                    stdin=stdin,
                    is_trial_run=is_trial_run,
                )
                self.assertIsNotNone(guidance)
                self.assertEqual(guidance['error_type'], expected_type)
                self.assertTrue(guidance['title'])
                self.assertTrue(guidance['summary'])
                self.assertGreaterEqual(len(guidance['attention']), 1)
                if expected_type != 'syntax_error':
                    self.assertEqual(guidance['raw'], stderr)

    def test_eof_empty_stdin_trial_run(self):
        guidance = explain_execution_error(
            EOF_TRACEBACK,
            source_code='name = input()',
            stdin='',
            is_trial_run=True,
        )
        self.assertEqual(guidance['error_type'], 'eof_error')
        self.assertIn('why', guidance)
        self.assertIn('input()', guidance['why'])
        self.assertIn('отдельный вопрос', guidance['why'])
        self.assertIn('>', guidance['attention'][0])

    def test_eof_insufficient_lines(self):
        guidance = explain_execution_error(
            EOF_TRACEBACK,
            source_code='a = input()\nb = input()',
            stdin='один',
            is_trial_run=True,
        )
        self.assertIn('2', guidance['summary'])
        self.assertIn('1', guidance['summary'])
        self.assertIn('why', guidance)
        self.assertIn('последний вопрос', guidance['attention'][0].lower())
        self.assertIn('лишний input()', guidance['attention'][2].lower())

    def test_eof_submit_extra_input(self):
        guidance = explain_execution_error(
            EOF_TRACEBACK,
            source_code='a = input()\nb = input()',
            stdin='Гоша',
            is_trial_run=False,
        )
        self.assertEqual(guidance['error_type'], 'eof_error')
        self.assertIn('тест', guidance['attention'][0].lower())
        self.assertIn('сдаче', guidance['why'].lower())

    def test_timeout_status(self):
        guidance = explain_execution_error(status='timeout')
        self.assertEqual(guidance['error_type'], 'timeout')
        self.assertIn('бесконечного цикла', guidance['attention'][0])

    def test_compile_error(self):
        guidance = explain_execution_error(
            stderr='',
            compile_output='error: cannot find symbol',
            status='compile_error',
        )
        self.assertEqual(guidance['error_type'], 'compile_error')

    def test_success_returns_none(self):
        self.assertIsNone(explain_execution_error(status='success'))

    def test_guidance_summary(self):
        guidance = explain_execution_error(SYNTAX_TRACEBACK, status='error')
        summary = guidance_summary(guidance).lower()
        self.assertTrue('синтаксис' in summary or 'разобрать' in summary)

    def test_is_waiting_for_input_repl_eof(self):
        self.assertTrue(
            is_waiting_for_input(
                source_code='name = input("Как тебя зовут? ")\nprint(name)',
                stdin='',
                run_status='error',
                stderr=EOF_TRACEBACK,
            )
        )
        self.assertTrue(
            is_waiting_for_input(
                source_code='a = input()\nb = input()',
                stdin='один\n',
                run_status='error',
                stderr=EOF_TRACEBACK,
            )
        )
        self.assertFalse(
            is_waiting_for_input(
                source_code='name = input()\nprint(name)',
                stdin='Гоша\n',
                run_status='success',
                stderr='',
            )
        )
        self.assertFalse(
            is_waiting_for_input(
                source_code='print("hi")',
                stdin='',
                run_status='error',
                stderr=EOF_TRACEBACK,
            )
        )
