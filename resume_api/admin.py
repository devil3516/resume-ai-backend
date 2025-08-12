from django.contrib import admin

# Register your models here.
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'original_filename')
    ordering = ('-created_at',)
    list_editable = ('original_filename',)

