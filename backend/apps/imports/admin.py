from django.contrib import admin

from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('import_type', 'file_name', 'user', 'status', 'created_at', 'finished_at')
    list_filter = ('import_type', 'status')
    search_fields = ('file_name', 'user__username')
    readonly_fields = ('result_json', 'errors_json', 'created_at', 'finished_at')
