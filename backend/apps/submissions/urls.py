from django.urls import path

from .views import (
    AdminSubmissionDetailView,
    AdminSubmissionListView,
    AdminSubmissionRecheckView,
    CodeRunView,
    MySubmissionsListView,
    SubmissionCreateView,
    SubmissionDetailView,
)

urlpatterns = [
    path('code/run', CodeRunView.as_view(), name='code-run'),
    path('submissions', SubmissionCreateView.as_view(), name='submissions'),
    path('submissions/me', MySubmissionsListView.as_view(), name='submissions-me'),
    path('submissions/<int:pk>', SubmissionDetailView.as_view(), name='submission-detail'),
    path('admin/submissions', AdminSubmissionListView.as_view(), name='admin-submissions'),
    path('admin/submissions/<int:pk>', AdminSubmissionDetailView.as_view(), name='admin-submission-detail'),
    path('admin/submissions/<int:pk>/recheck', AdminSubmissionRecheckView.as_view(), name='admin-submission-recheck'),
]
