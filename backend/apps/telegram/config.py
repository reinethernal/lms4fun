from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings as django_settings

from .models import TelegramBotSettings

logger = logging.getLogger('apps.telegram')


@dataclass(frozen=True)
class TelegramRuntimeConfig:
    enabled: bool
    bot_token: str
    bot_username: str
    http_proxy: str
    notify_all_submissions: bool

    @property
    def is_ready(self) -> bool:
        return bool(self.enabled and self.bot_token.strip())


def get_telegram_config() -> TelegramRuntimeConfig:
    """Load bot config from DB (admin panel). Falls back to empty if table missing."""
    try:
        row = TelegramBotSettings.load()
    except Exception:
        logger.exception('Failed to load TelegramBotSettings')
        return TelegramRuntimeConfig(
            enabled=False,
            bot_token='',
            bot_username='',
            http_proxy='',
            notify_all_submissions=False,
        )
    return TelegramRuntimeConfig(
        enabled=row.enabled,
        bot_token=(row.bot_token or '').strip(),
        bot_username=(row.bot_username or '').strip().lstrip('@'),
        http_proxy=(row.http_proxy or '').strip(),
        notify_all_submissions=bool(row.notify_all_submissions),
    )


def seed_settings_from_env_if_empty() -> TelegramBotSettings:
    """One-time seed from legacy .env values when the row is first created empty."""
    row = TelegramBotSettings.load()
    if row.bot_token or row.enabled:
        return row
    env_token = getattr(django_settings, 'TELEGRAM_BOT_TOKEN', '') or ''
    env_enabled = getattr(django_settings, 'TELEGRAM_BOT_ENABLED', False)
    if not env_token and not env_enabled:
        return row
    row.enabled = bool(env_enabled)
    row.bot_token = env_token
    row.bot_username = getattr(django_settings, 'TELEGRAM_BOT_USERNAME', '') or ''
    row.http_proxy = getattr(django_settings, 'TELEGRAM_HTTP_PROXY', '') or ''
    row.notify_all_submissions = getattr(django_settings, 'TELEGRAM_NOTIFY_ALL_SUBMISSIONS', False)
    row.save()
    return row
