from django.contrib import admin

from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'number', 'status', 'sort_order')
    list_filter = ('status', 'course')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
