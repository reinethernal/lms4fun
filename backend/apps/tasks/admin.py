from django.contrib import admin

from .models import Task, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'checker_type', 'max_xp', 'sort_order')
    list_filter = ('checker_type', 'task_type', 'difficulty')
    search_fields = ('title',)
    inlines = [TestCaseInline]


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('task', 'sort_order', 'is_hidden')
