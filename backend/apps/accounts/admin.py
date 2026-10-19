from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Group, GroupUser, User


class GroupUserInline(admin.TabularInline):
    model = GroupUser
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'display_name', 'role', 'is_active', 'last_login')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'display_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('CodeLearn', {'fields': ('display_name', 'role', 'avatar', 'children')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('CodeLearn', {'fields': ('email', 'display_name', 'role')}),
    )
    filter_horizontal = ('children',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    inlines = [GroupUserInline]


@admin.register(GroupUser)
class GroupUserAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'joined_at')
    list_filter = ('group',)
