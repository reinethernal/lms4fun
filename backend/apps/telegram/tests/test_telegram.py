from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.telegram.config import get_telegram_config
from apps.telegram.formatting import format_submission_card, review_keyboard
from apps.telegram.models import TelegramAccount, TelegramBotSettings, TelegramLinkCode
from apps.telegram.services import link_account, unlink_account

User = get_user_model()


class TelegramFormattingTests(SimpleTestCase):
    def test_review_keyboard_structure(self):
        kb = review_keyboard(42)
        self.assertIn('inline_keyboard', kb)
        flat = [btn['callback_data'] for row in kb['inline_keyboard'] for btn in row]
        self.assertIn('rv:42:accept', flat)
        self.assertIn('rv:42:reject', flat)
        self.assertIn('rv:42:comment', flat)

    def test_submission_card_contains_lms_student_profile_link(self):
        submission = SimpleNamespace(
            id=7,
            user_id=11,
            user=SimpleNamespace(display_name='Иван', username='ivan'),
            task=SimpleNamespace(
                title='FizzBuzz',
                lesson=SimpleNamespace(
                    title='Циклы',
                    course=SimpleNamespace(title='Python Basics'),
                ),
            ),
            status='manual_review',
            submitted_at=timezone.now(),
            teacher_comment='',
            code='print("ok")',
        )
        card = format_submission_card(submission)
        self.assertIn('/students/11', card)
        self.assertIn('>Иван</a>', card)
        self.assertNotIn('@ivan', card)


class TelegramConfigTests(TestCase):
    def test_settings_in_db(self):
        row = TelegramBotSettings.load()
        row.enabled = True
        row.bot_token = '123:ABC'
        row.bot_username = '@demo_bot'
        row.http_proxy = 'http://proxy:8080'
        row.notify_all_submissions = True
        row.save()

        cfg = get_telegram_config()
        self.assertTrue(cfg.is_ready)
        self.assertEqual(cfg.bot_username, 'demo_bot')
        self.assertEqual(cfg.http_proxy, 'http://proxy:8080')
        self.assertTrue(cfg.notify_all_submissions)


class TelegramLinkTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='t1@example.com',
            password='pass',
            role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username='student1',
            email='s1@example.com',
            password='pass',
            role=User.Role.STUDENT,
        )
        row = TelegramBotSettings.load()
        row.enabled = True
        row.bot_token = 'token'
        row.save()

    def test_link_and_unlink(self):
        code = TelegramLinkCode.create_for_user(self.teacher)
        account = link_account(code.code, chat_id=123456, telegram_username='teach')
        self.assertEqual(account.user_id, self.teacher.id)
        self.assertEqual(account.chat_id, 123456)
        self.assertTrue(unlink_account(123456))
        self.assertFalse(TelegramAccount.objects.filter(chat_id=123456, is_active=True).exists())

    def test_student_cannot_link(self):
        code = TelegramLinkCode.create_for_user(self.student)
        with self.assertRaises(ValueError):
            link_account(code.code, chat_id=99)

    def test_expired_code(self):
        code = TelegramLinkCode.create_for_user(self.teacher)
        code.expires_at = timezone.now() - timedelta(minutes=1)
        code.save(update_fields=['expires_at'])
        with self.assertRaises(ValueError):
            link_account(code.code, chat_id=1)


class TelegramSettingsApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1',
            email='a1@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.teacher = User.objects.create_user(
            username='teacher2',
            email='t2@example.com',
            password='pass',
            role=User.Role.TEACHER,
        )
        self.client = APIClient()

    def test_admin_can_update_settings(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put('/api/telegram/settings', {
            'enabled': True,
            'bot_token': '999:SECRET',
            'bot_username': 'platform_bot',
            'http_proxy': 'http://127.0.0.1:3128',
            'notify_all_submissions': True,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['enabled'])
        self.assertTrue(response.data['bot_token_set'])
        self.assertTrue(response.data['is_ready'])
        self.assertEqual(response.data['bot_username'], 'platform_bot')
        self.assertNotIn('SECRET', response.data.get('bot_token_masked', ''))

        row = TelegramBotSettings.load()
        self.assertEqual(row.bot_token, '999:SECRET')
        self.assertEqual(row.http_proxy, 'http://127.0.0.1:3128')

    def test_teacher_cannot_update_settings(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.put('/api/telegram/settings', {'enabled': True}, format='json')
        self.assertEqual(response.status_code, 403)
