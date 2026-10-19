from django.conf import settings
from django.db import models


class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_records')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='user_progress')
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True)
    xp_earned = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    last_activity_at = models.DateTimeField(auto_now=True)
    progress_json = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [['user', 'course']]
        ordering = ['-last_activity_at']

    def __str__(self):
        return f'{self.user} — {self.course} ({self.xp_earned} XP)'


class XPTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='xp_transactions')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_granted',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} +{self.amount} XP'


class UserSkillStats(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_stats')
    stats_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Stats for {self.user}'


class Badge(models.Model):
    class BadgeType(models.TextChoices):
        ACHIEVEMENT = 'achievement', 'Достижение'
        COURSE = 'course', 'Курс'
        LANGUAGE = 'language', 'Язык'
        SPECIAL = 'special', 'Особый'
        PROJECT = 'project', 'Проект'
        STYLE = 'style', 'Стиль'
        DEBUG = 'debug', 'Отладка'
        SOFT_SKILL = 'soft_skill', 'Навык'
        SOCIAL = 'social', 'Социальный'
        FINAL_PROJECT = 'final_project', 'Финальный проект'

    class BadgeLevel(models.TextChoices):
        BRONZE = 'bronze', 'Бронза'
        SILVER = 'silver', 'Серебро'
        GOLD = 'gold', 'Золото'
        PLATINUM = 'platinum', 'Платина'
        LEGENDARY = 'legendary', 'Легенда'

    class ConditionType(models.TextChoices):
        XP_TOTAL = 'xp_total', 'Всего XP'
        TASKS_COMPLETED = 'tasks_completed', 'Заданий выполнено'
        LESSONS_COMPLETED = 'lessons_completed', 'Уроков пройдено'
        COURSE_COMPLETED = 'course_completed', 'Курс завершён'
        MANUAL = 'manual', 'Вручную'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=255, blank=True, help_text='URL или emoji (если нет загруженной иконки)')
    icon_image = models.ImageField(upload_to='badges/', blank=True, null=True)
    badge_type = models.CharField(max_length=20, choices=BadgeType.choices, default=BadgeType.ACHIEVEMENT)
    level = models.CharField(max_length=20, choices=BadgeLevel.choices, default=BadgeLevel.BRONZE, blank=True)
    condition_type = models.CharField(max_length=30, choices=ConditionType.choices, blank=True)
    condition_key = models.CharField(max_length=64, blank=True)
    condition_value = models.IntegerField(null=True, blank=True)
    condition_params = models.JSONField(default=dict, blank=True)
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def icon_url(self):
        if self.icon_image:
            return self.icon_image.url
        return self.icon or ''

    def effective_condition_key(self) -> str:
        if self.condition_key:
            return self.condition_key
        if self.condition_type and self.condition_type != self.ConditionType.MANUAL:
            return self.condition_type
        return ''


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges_awarded',
    )

    class Meta:
        unique_together = [['user', 'badge']]
        ordering = ['-awarded_at']

    def __str__(self):
        return f'{self.user} — {self.badge}'
