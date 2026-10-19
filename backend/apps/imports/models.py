from django.conf import settings
from django.db import models


class ImportJob(models.Model):
    class ImportType(models.TextChoices):
        COURSE = 'course', 'Курс'
        LESSON = 'lesson', 'Урок'
        TASKS = 'tasks', 'Задания'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        PROCESSING = 'processing', 'Обработка'
        COMPLETED = 'completed', 'Завершено'
        FAILED = 'failed', 'Ошибка'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='import_jobs')
    import_type = models.CharField(max_length=20, choices=ImportType.choices)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    result_json = models.JSONField(default=dict, blank=True)
    errors_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.import_type} — {self.file_name} ({self.status})'
