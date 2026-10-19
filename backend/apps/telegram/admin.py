from django.contrib import admin

from .models import TelegramAccount, TelegramBotSettings, TelegramLinkCode


@admin.register(TelegramBotSettings)
class TelegramBotSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'enabled', 'bot_username', 'notify_all_submissions', 'updated_at')
    fields = (
        'enabled',
        'bot_token',
        'bot_username',
        'http_proxy',
        'notify_all_submissions',
        'updated_at',
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not TelegramBotSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_id', 'telegram_username', 'is_active', 'notify_manual_review', 'linked_at')
    list_filter = ('is_active', 'notify_manual_review', 'notify_new_submissions')
    search_fields = ('user__username', 'user__email', 'telegram_username', 'chat_id')


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'expires_at', 'used_at', 'created_at')
    search_fields = ('code', 'user__username')
