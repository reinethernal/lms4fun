import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class TelegramBotSettings(models.Model):
    """Singleton platform settings for the Telegram review bot (editable in admin UI)."""

    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    enabled = models.BooleanField('Бот включён', default=False)
    bot_token = models.CharField('Токен бота', max_length=255, blank=True)
    bot_username = models.CharField('Username бота', max_length=255, blank=True, help_text='Без @')
    http_proxy = models.CharField(
        'HTTP(S) proxy',
        max_length=512,
        blank=True,
        help_text='Например http://user:pass@host:8080',
    )
    notify_all_submissions = models.BooleanField(
        'Уведомлять обо всех решениях',
        default=False,
        help_text='Если выключено — только решения на ручной проверке (manual_review).',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки Telegram-бота'
        verbose_name_plural = 'Настройки Telegram-бота'

    def __str__(self):
        state = 'включён' if self.enabled else 'выключен'
        return f'Telegram-бот ({state})'

    def save(self, *args, **kwargs):
        self.singleton_id = 1
        self.bot_username = (self.bot_username or '').lstrip('@').strip()
        self.http_proxy = (self.http_proxy or '').strip()
        self.bot_token = (self.bot_token or '').strip()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> 'TelegramBotSettings':
        obj, _ = cls.objects.get_or_create(singleton_id=1)
        return obj

    @property
    def is_ready(self) -> bool:
        return bool(self.enabled and self.bot_token)


class TelegramAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_account',
    )
    chat_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=255, blank=True)
    notify_new_submissions = models.BooleanField(default=True)
    notify_manual_review = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-linked_at']

    def __str__(self):
        return f'{self.user} → {self.chat_id}'


def _default_link_expiry():
    return timezone.now() + timedelta(hours=24)


class TelegramLinkCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_link_codes',
    )
    code = models.CharField(max_length=16, unique=True, db_index=True)
    expires_at = models.DateTimeField(default=_default_link_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.user})'

    @classmethod
    def create_for_user(cls, user) -> 'TelegramLinkCode':
        code = secrets.token_hex(4).upper()
        while cls.objects.filter(code=code, used_at__isnull=True, expires_at__gt=timezone.now()).exists():
            code = secrets.token_hex(4).upper()
        return cls.objects.create(user=user, code=code)

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()
