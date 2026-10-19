from django.contrib.auth.models import AbstractUser
from django.db import models

from .avatar import avatar_upload_path


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Суперадминистратор'
        ADMIN = 'admin', 'Администратор'
        TEACHER = 'teacher', 'Преподаватель'
        STUDENT = 'student', 'Ученик'
        PARENT = 'parent', 'Родитель'

    email = models.EmailField('email', unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    avatar = models.URLField(blank=True)
    avatar_image = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    children = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parents',
        limit_choices_to={'role': Role.STUDENT},
    )

    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.display_name or self.username

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN or self.is_superuser

    @property
    def is_platform_admin(self):
        return self.role in (self.Role.SUPERADMIN, self.Role.ADMIN) or self.is_superuser

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT


class Group(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_groups',
        limit_choices_to={'role__in': [User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPERADMIN]},
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class GroupUser(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['group', 'user']]
        ordering = ['joined_at']

    def __str__(self):
        return f'{self.user} in {self.group}'
