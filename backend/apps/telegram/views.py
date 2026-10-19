from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPlatformAdmin, IsStaffMember

from .config import get_telegram_config, seed_settings_from_env_if_empty
from .models import TelegramAccount, TelegramBotSettings, TelegramLinkCode
from .services import telegram_enabled


def _mask_token(token: str) -> str:
    token = (token or '').strip()
    if not token:
        return ''
    if len(token) <= 8:
        return '*' * len(token)
    return f'{token[:4]}…{token[-4:]}'


def _serialize_bot_settings(row: TelegramBotSettings) -> dict:
    return {
        'enabled': row.enabled,
        'bot_token_set': bool(row.bot_token),
        'bot_token_masked': _mask_token(row.bot_token),
        'bot_username': row.bot_username,
        'http_proxy': row.http_proxy,
        'notify_all_submissions': row.notify_all_submissions,
        'is_ready': row.is_ready,
        'updated_at': row.updated_at,
    }


class TelegramBotSettingsSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(required=False)
    bot_token = serializers.CharField(required=False, allow_blank=True, max_length=255)
    clear_bot_token = serializers.BooleanField(required=False, default=False)
    bot_username = serializers.CharField(required=False, allow_blank=True, max_length=255)
    http_proxy = serializers.CharField(required=False, allow_blank=True, max_length=512)
    notify_all_submissions = serializers.BooleanField(required=False)


class TelegramBotSettingsView(APIView):
    """Platform admins configure bot token / proxy / toggles in the admin UI."""

    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        seed_settings_from_env_if_empty()
        return Response(_serialize_bot_settings(TelegramBotSettings.load()))

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        serializer = TelegramBotSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        row = TelegramBotSettings.load()

        if 'enabled' in data:
            row.enabled = data['enabled']
        if 'bot_username' in data:
            row.bot_username = data['bot_username']
        if 'http_proxy' in data:
            row.http_proxy = data['http_proxy']
        if 'notify_all_submissions' in data:
            row.notify_all_submissions = data['notify_all_submissions']
        if data.get('clear_bot_token'):
            row.bot_token = ''
        elif 'bot_token' in data and data['bot_token'].strip():
            row.bot_token = data['bot_token'].strip()

        row.save()
        return Response(_serialize_bot_settings(row))


class TelegramMeView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        seed_settings_from_env_if_empty()
        cfg = get_telegram_config()
        account = TelegramAccount.objects.filter(user=request.user, is_active=True).first()
        payload = {
            'enabled': telegram_enabled(),
            'linked': bool(account),
            'chat_id': account.chat_id if account else None,
            'telegram_username': account.telegram_username if account else '',
            'bot_username': cfg.bot_username,
            'notify_manual_review': account.notify_manual_review if account else True,
            'notify_new_submissions': account.notify_new_submissions if account else True,
            'can_manage_bot': bool(request.user.is_platform_admin),
            'notify_all_submissions': cfg.notify_all_submissions,
        }
        return Response(payload)

    def patch(self, request):
        account = TelegramAccount.objects.filter(user=request.user, is_active=True).first()
        if account is None:
            return Response({'detail': 'Telegram не привязан.'}, status=status.HTTP_400_BAD_REQUEST)
        for field in ('notify_manual_review', 'notify_new_submissions'):
            if field in request.data:
                setattr(account, field, bool(request.data[field]))
        account.save()
        return self.get(request)

    def delete(self, request):
        updated = TelegramAccount.objects.filter(user=request.user, is_active=True).update(is_active=False)
        if not updated:
            return Response({'detail': 'Привязка не найдена.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'Telegram отвязан.'})


class TelegramLinkCodeCreateView(APIView):
    permission_classes = [IsStaffMember]

    def post(self, request):
        if not telegram_enabled():
            return Response(
                {'detail': 'Telegram-бот выключен. Администратор должен настроить его в панели.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (request.user.is_platform_admin or request.user.is_teacher):
            return Response({'detail': 'Недостаточно прав.'}, status=status.HTTP_403_FORBIDDEN)
        link = TelegramLinkCode.create_for_user(request.user)
        return Response({
            'code': link.code,
            'expires_at': link.expires_at,
            'start_command': f'/start {link.code}',
        }, status=status.HTTP_201_CREATED)
