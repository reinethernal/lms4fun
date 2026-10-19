from django.contrib import admin

from .models import CodeRun, Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'status', 'xp_awarded', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'task__title')
    readonly_fields = ('checker_result', 'submitted_at', 'checked_at')


@admin.register(CodeRun)
class CodeRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'status', 'execution_time', 'created_at')
    list_filter = ('status', 'language')
    readonly_fields = ('created_at',)
