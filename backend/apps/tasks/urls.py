from django.urls import path

from .views import AdminTaskDetailView, AdminTaskListCreateView, LessonTasksView

urlpatterns = [
    path('lessons/<int:pk>/tasks', LessonTasksView.as_view(), name='lesson-tasks'),
    path('admin/tasks', AdminTaskListCreateView.as_view(), name='admin-tasks'),
    path('admin/tasks/<int:pk>', AdminTaskDetailView.as_view(), name='admin-task-detail'),
]
