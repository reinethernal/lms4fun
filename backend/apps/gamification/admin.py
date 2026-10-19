from django.contrib import admin

from .models import Badge, UserBadge, UserProgress, UserSkillStats, XPTransaction


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'xp_earned', 'tasks_completed', 'last_activity_at')
    list_filter = ('course',)


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reason', 'course', 'created_at')
    list_filter = ('course',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_type', 'level', 'condition_key', 'is_active', 'has_icon')
    list_filter = ('badge_type', 'level', 'is_active')
    readonly_fields = ('icon_preview',)

    @admin.display(boolean=True, description='Иконка')
    def has_icon(self, obj):
        return bool(obj.icon_image or obj.icon)

    @admin.display(description='Превью')
    def icon_preview(self, obj):
        from django.utils.html import format_html

        if obj.icon_image:
            return format_html('<img src="{}" style="max-height:64px" />', obj.icon_image.url)
        if obj.icon:
            return obj.icon
        return '—'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')


@admin.register(UserSkillStats)
class UserSkillStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
