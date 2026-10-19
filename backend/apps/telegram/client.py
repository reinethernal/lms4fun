"""Low-level Telegram Bot API client with HTTP(S) proxy support."""
from __future__ import annotations

import logging
from typing import Any

import requests

from .config import get_telegram_config

logger = logging.getLogger('apps.telegram')


class TelegramApiError(Exception):
    def __init__(self, message: str, *, response: dict | None = None):
        super().__init__(message)
        self.response = response or {}


class TelegramApiClient:
    def __init__(self, token: str | None = None, proxy_url: str | None = None):
        cfg = get_telegram_config()
        self.token = token if token is not None else cfg.bot_token
        self.proxy_url = proxy_url if proxy_url is not None else cfg.http_proxy
        self._enabled = cfg.enabled
        self.session = requests.Session()
        if self.proxy_url:
            self.session.proxies.update({
                'http': self.proxy_url,
                'https': self.proxy_url,
            })

    @property
    def enabled(self) -> bool:
        return bool(self.token) and self._enabled

    def _url(self, method: str) -> str:
        return f'https://api.telegram.org/bot{self.token}/{method}'

    def call(self, method: str, payload: dict[str, Any] | None = None, *, files=None) -> dict[str, Any]:
        if not self.token:
            raise TelegramApiError('Токен Telegram-бота не задан в настройках')
        try:
            response = self.session.post(
                self._url(method),
                json=payload if files is None else None,
                data=payload if files is not None else None,
                files=files,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception('Telegram API request failed: %s', method)
            raise TelegramApiError(str(exc)) from exc

        if not data.get('ok'):
            raise TelegramApiError(data.get('description', 'Telegram API error'), response=data)
        return data.get('result', {})

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_markup: dict | None = None,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
        }
        if reply_markup is not None:
            payload['reply_markup'] = reply_markup
        return self.call('sendMessage', payload)

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        *,
        reply_markup: dict | None = None,
        parse_mode: str = 'HTML',
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
        }
        if reply_markup is not None:
            payload['reply_markup'] = reply_markup
        return self.call('editMessageText', payload)

    def answer_callback_query(self, callback_query_id: str, text: str = '', *, show_alert: bool = False):
        return self.call('answerCallbackQuery', {
            'callback_query_id': callback_query_id,
            'text': text[:200],
            'show_alert': show_alert,
        })
