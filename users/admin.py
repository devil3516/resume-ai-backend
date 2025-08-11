from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    
    # Fields to display in the user edit form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'profile_picture')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login',)}),
        ('Statistics', {'fields': ('resume_analyzed', 'job_analyzed', 'cover_letters', 'success_rate')}),
    )
    
    # Fields to display when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    
    # Fields to display in the list view (read-only)
    list_display = ('email', 'name', 'is_staff', 'is_active', 'date_joined', 'resume_analyzed', 'job_analyzed', 'cover_letters', 'success_rate')
    
    # Fields to filter by
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    
    # Fields to search by
    search_fields = ('email', 'name')
    
    # Default ordering
    ordering = ('email',)
    
    # Make these fields editable in the list view
    list_editable = ('is_active', 'is_staff')
    
    # Number of items to display per page
    list_per_page = 20
    
    # Make statistics fields read-only in admin
    readonly_fields = ('date_joined', 'resume_analyzed', 'job_analyzed', 'cover_letters', 'success_rate')
