from django.urls import path

from .views import TelegramBotSettingsView, TelegramLinkCodeCreateView, TelegramMeView

urlpatterns = [
    path('telegram/me', TelegramMeView.as_view(), name='telegram-me'),
    path('telegram/link-code', TelegramLinkCodeCreateView.as_view(), name='telegram-link-code'),
    path('telegram/settings', TelegramBotSettingsView.as_view(), name='telegram-settings'),
]
