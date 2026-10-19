from django.contrib import admin

from .models import Course, CourseAssignment, ProgrammingLanguage


@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'judge0_language_id', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'primary_language', 'status', 'visibility', 'author')
    list_filter = ('status', 'visibility', 'primary_language')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'user', 'group', 'status', 'assigned_by', 'created_at')
    list_filter = ('status',)
