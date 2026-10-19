from django.urls import path

from .views import (
    AdminBadgeDetailView,
    AdminBadgeListCreateView,
    LeaderboardView,
    MyBadgesView,
    MyProgressView,
)

urlpatterns = [
    path('progress/me', MyProgressView.as_view(), name='progress-me'),
    path('leaderboard', LeaderboardView.as_view(), name='leaderboard'),
    path('badges/me', MyBadgesView.as_view(), name='badges-me'),
    path('admin/badges', AdminBadgeListCreateView.as_view(), name='admin-badges'),
    path('admin/badges/<int:pk>', AdminBadgeDetailView.as_view(), name='admin-badge-detail'),
]
