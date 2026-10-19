from django.db import models


class Task(models.Model):
    class TaskType(models.TextChoices):
        PRACTICE = 'practice', 'Практика'
        QUIZ = 'quiz', 'Тест'
        PROJECT = 'project', 'Проект'
        CHALLENGE = 'challenge', 'Задача'

    class CheckerType(models.TextChoices):
        STDOUT_EXACT = 'stdout_exact', 'Точное совпадение stdout'
        STDOUT_REGEX = 'stdout_regex', 'Регулярное выражение stdout'
        STDIN_STDOUT = 'stdin_stdout', 'Тесты stdin/stdout'
        CUSTOM = 'custom', 'Пользовательская проверка'
        MANUAL = 'manual', 'Ручная проверка'

    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.CASCADE, related_name='tasks')
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.PROTECT, related_name='tasks')
    slug = models.SlugField(max_length=120, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.PRACTICE)
    starter_code = models.TextField(blank=True)
    solution_template = models.TextField(blank=True)
    stdin = models.TextField(blank=True)
    expected_stdout = models.TextField(blank=True)
    expected_stderr = models.TextField(blank=True)
    checker_type = models.CharField(max_length=30, choices=CheckerType.choices, default=CheckerType.STDOUT_EXACT)
    checker_code = models.TextField(blank=True)
    visible_tests_json = models.JSONField(default=list, blank=True)
    hidden_tests_json = models.JSONField(default=list, blank=True)
    checker_config_json = models.JSONField(default=dict, blank=True)
    max_xp = models.IntegerField(default=5)
    difficulty = models.CharField(max_length=20, default='easy')
    is_required = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        unique_together = [['lesson', 'slug']]

    def __str__(self):
        return self.title


class TestCase(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='test_cases')
    stdin = models.TextField(blank=True)
    expected_stdout = models.TextField(blank=True)
    expected_stderr = models.TextField(blank=True)
    is_hidden = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'Test #{self.sort_order} for {self.task}'
