from django.urls import path

from .profile_views import ProfileMeView, StudentProfileView
from .submission_views import StudentSubmissionsListView
from .views import (
    AdminGroupDetailView,
    AdminGroupListCreateView,
    AdminUserBadgesView,
    AdminUserBadgeRevokeView,
    AdminUserDetailView,
    AdminUserListCreateView,
    AdminUserResetStatisticsView,
    LoginView,
    LogoutView,
    MeView,
)
from .parent_views import (
    ParentChildBadgesView,
    ParentChildPasswordView,
    ParentChildProgressView,
    ParentChildSubmissionDetailView,
    ParentChildSubmissionsListView,
    ParentChildrenListCreateView,
)

from .staff_views import (
    StaffParentChildrenView,
    StaffParentsListView,
    StaffStudentsListView,
)

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/logout', LogoutView.as_view(), name='auth-logout'),
    path('me', MeView.as_view(), name='me'),
    path('profile/me', ProfileMeView.as_view(), name='profile-me'),
    path('students/<int:pk>/profile', StudentProfileView.as_view(), name='student-profile'),
    path('students/<int:pk>/submissions', StudentSubmissionsListView.as_view(), name='student-submissions'),
    path('admin/users', AdminUserListCreateView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:pk>/reset-statistics', AdminUserResetStatisticsView.as_view(), name='admin-user-reset-statistics'),
    path('admin/users/<int:pk>/badges', AdminUserBadgesView.as_view(), name='admin-user-badges'),
    path('admin/users/<int:pk>/badges/<int:badge_id>', AdminUserBadgeRevokeView.as_view(), name='admin-user-badge-revoke'),
    path('admin/groups', AdminGroupListCreateView.as_view(), name='admin-groups'),
    path('admin/groups/<int:pk>', AdminGroupDetailView.as_view(), name='admin-group-detail'),
    path('parent/children', ParentChildrenListCreateView.as_view(), name='parent-children'),
    path('parent/children/<int:child_id>/password', ParentChildPasswordView.as_view(), name='parent-child-password'),
    path('parent/children/<int:child_id>/progress', ParentChildProgressView.as_view(), name='parent-child-progress'),
    path('parent/children/<int:child_id>/badges', ParentChildBadgesView.as_view(), name='parent-child-badges'),
    path('parent/children/<int:child_id>/submissions', ParentChildSubmissionsListView.as_view(), name='parent-child-submissions'),
    path(
        'parent/children/<int:child_id>/submissions/<int:pk>',
        ParentChildSubmissionDetailView.as_view(),
        name='parent-child-submission-detail',
    ),
    path('staff/parents', StaffParentsListView.as_view(), name='staff-parents'),
    path('staff/students', StaffStudentsListView.as_view(), name='staff-students'),
    path('staff/parents/<int:pk>/children', StaffParentChildrenView.as_view(), name='staff-parent-children'),
]
