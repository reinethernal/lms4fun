from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        LESSON_COMPLETED = 'lesson_completed', 'Урок выполнен'
        BADGE_EARNED = 'badge_earned', 'Получен бейдж'
        SUBMISSION_ACCEPTED = 'submission_accepted', 'Решение принято'
        SUBMISSION_REJECTED = 'submission_rejected', 'Решение отклонено'
        LESSON_UNLOCKED = 'lesson_unlocked', 'Открыт новый урок'
        XP_EARNED = 'xp_earned', 'Получены XP'
        COURSE_ASSIGNED = 'course_assigned', 'Назначен курс'
        TEACHER_COMMENT = 'teacher_comment', 'Комментарий преподавателя'
        SYSTEM = 'system', 'Системное'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    data_json = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.title}'


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.CharField(max_length=50, blank=True)
    details_json = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} ({self.entity_type}:{self.entity_id})'
