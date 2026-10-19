from django.urls import path

from .views import (
    AdminCourseAssignmentDetailView,
    AdminCourseAssignmentListCreateView,
    AdminCourseDetailView,
    AdminCourseListCreateView,
    AdminLanguageDetailView,
    AdminLanguageListCreateView,
    CourseDetailView,
    CourseListView,
    LanguageListView,
)

urlpatterns = [
    path('languages', LanguageListView.as_view(), name='languages'),
    path('courses', CourseListView.as_view(), name='courses'),
    path('courses/<int:pk>', CourseDetailView.as_view(), name='course-detail'),
    path('admin/courses', AdminCourseListCreateView.as_view(), name='admin-courses'),
    path('admin/courses/<int:pk>', AdminCourseDetailView.as_view(), name='admin-course-detail'),
    path('admin/languages', AdminLanguageListCreateView.as_view(), name='admin-languages'),
    path('admin/languages/<int:pk>', AdminLanguageDetailView.as_view(), name='admin-language-detail'),
    path('admin/course-assignments', AdminCourseAssignmentListCreateView.as_view(), name='admin-course-assignments'),
    path('admin/course-assignments/<int:pk>', AdminCourseAssignmentDetailView.as_view(), name='admin-course-assignment-detail'),
]
