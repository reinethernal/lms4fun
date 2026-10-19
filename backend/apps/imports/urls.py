from django.urls import path

from .views import (
    ExportCourseView,
    ExportLeaderboardView,
    ImportCourseView,
    ImportJobListView,
    ImportLessonView,
    ImportTasksView,
)

urlpatterns = [
    path('admin/import/course', ImportCourseView.as_view(), name='admin-import-course'),
    path('admin/import/lesson', ImportLessonView.as_view(), name='admin-import-lesson'),
    path('admin/import/tasks', ImportTasksView.as_view(), name='admin-import-tasks'),
    path('admin/import/jobs', ImportJobListView.as_view(), name='admin-import-jobs'),
    path('admin/export/course/<int:pk>', ExportCourseView.as_view(), name='admin-export-course'),
    path('admin/export/leaderboard', ExportLeaderboardView.as_view(), name='admin-export-leaderboard'),
]
