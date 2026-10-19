from django.urls import path

from .views import (
    AdminLessonDetailView,
    AdminLessonListCreateView,
    CourseLessonsView,
    LessonDetailView,
)

urlpatterns = [
    path('courses/<int:pk>/lessons', CourseLessonsView.as_view(), name='course-lessons'),
    path('lessons/<int:pk>', LessonDetailView.as_view(), name='lesson-detail'),
    path('admin/lessons', AdminLessonListCreateView.as_view(), name='admin-lessons'),
    path('admin/lessons/<int:pk>', AdminLessonDetailView.as_view(), name='admin-lesson-detail'),
]
