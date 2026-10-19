from django.conf import settings
from django.db import models


class Submission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        RUNNING = 'running', 'Проверяется'
        ACCEPTED = 'accepted', 'Принято'
        WRONG_ANSWER = 'wrong_answer', 'Неверный ответ'
        RUNTIME_ERROR = 'runtime_error', 'Ошибка выполнения'
        COMPILE_ERROR = 'compile_error', 'Ошибка компиляции'
        TIME_LIMIT = 'time_limit', 'Превышен лимит времени'
        REJECTED = 'rejected', 'Отклонено'
        MANUAL_REVIEW = 'manual_review', 'Ручная проверка'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='submissions')
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.PROTECT)
    code = models.TextField()
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    compile_output = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    score = models.IntegerField(default=0)
    xp_awarded = models.IntegerField(default=0)
    checker_result = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions',
    )
    teacher_comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.user} — {self.task} ({self.status})'


class CodeRun(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успех'
        ERROR = 'error', 'Ошибка'
        TIMEOUT = 'timeout', 'Таймаут'
        COMPILE_ERROR = 'compile_error', 'Ошибка компиляции'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='code_runs')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.PROTECT)
    source_code = models.TextField()
    stdin = models.TextField(blank=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    compile_output = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Run by {self.user} at {self.created_at}'
