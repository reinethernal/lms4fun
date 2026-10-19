from django.conf import settings
from django.db import models


class Lesson(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликован'
        ARCHIVED = 'archived', 'Архив'

    class ContentFormat(models.TextChoices):
        MARKDOWN = 'markdown', 'Markdown'
        HTML = 'html', 'HTML'
        JSON = 'json', 'JSON'

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='lessons')
    language = models.ForeignKey('courses.ProgrammingLanguage', on_delete=models.PROTECT, related_name='lessons')
    number = models.IntegerField()
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    goal = models.TextField(blank=True)
    theory_text = models.TextField(blank=True)
    simple_explanation = models.TextField(blank=True)
    practice_text = models.TextField(blank=True)
    mini_project_text = models.TextField(blank=True)
    summary_text = models.TextField(blank=True)
    max_xp = models.IntegerField(default=0)
    badge = models.ForeignKey(
        'gamification.Badge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_lessons',
    )
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    content_format = models.CharField(max_length=20, choices=ContentFormat.choices, default=ContentFormat.MARKDOWN)
    source_import_id = models.CharField(max_length=100, blank=True)
    assets_json = models.JSONField(default=list, blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['course', 'slug']]
        ordering = ['sort_order', 'number']

    def __str__(self):
        return f'{self.course.title} — {self.title}'
