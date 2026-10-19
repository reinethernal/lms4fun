import time

from django.core.management.base import BaseCommand

from apps.telegram.bot import build_application
from apps.telegram.config import get_telegram_config, seed_settings_from_env_if_empty


class Command(BaseCommand):
    help = 'Run Telegram bot long-polling (teachers/admins review submissions)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wait',
            action='store_true',
            default=True,
            help='Wait until bot is enabled and token is set in admin panel',
        )
        parser.add_argument('--no-wait', action='store_false', dest='wait')

    def handle(self, *args, **options):
        seed_settings_from_env_if_empty()
        wait = options['wait']

        while True:
            cfg = get_telegram_config()
            if cfg.is_ready:
                break
            msg = (
                'Telegram-бот выключен или токен не задан. '
                'Настройте его в админ-панели платформы.'
            )
            if not wait:
                self.stderr.write(self.style.ERROR(msg))
                return
            self.stdout.write(msg + ' Ожидание 15 с…')
            time.sleep(15)

        cfg = get_telegram_config()
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot…'))
        if cfg.bot_username:
            self.stdout.write(f'Bot: @{cfg.bot_username}')
        if cfg.http_proxy:
            self.stdout.write(f'Using HTTP proxy: {cfg.http_proxy}')
        else:
            self.stdout.write('HTTP proxy: not set')

        app = build_application()
        app.run_polling(drop_pending_updates=True, allowed_updates=['message', 'callback_query'])
