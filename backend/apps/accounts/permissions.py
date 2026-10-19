from rest_framework import permissions

from .models import User


class IsPlatformAdmin(permissions.BasePermission):
    """Superadmin or admin."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_platform_admin
        )


class IsStaffMember(permissions.BasePermission):
    """Superadmin, admin, or teacher."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_platform_admin or request.user.is_teacher


class IsParent(permissions.BasePermission):
    """Parent role only."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_parent
        )


class IsStudentOrStaff(permissions.BasePermission):
    """Students and staff; parents excluded from code/submission endpoints."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_parent:
            return False
        return True
