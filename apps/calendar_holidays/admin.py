"""
Calendar & Holidays App Admin - Holiday Administration
"""
from django.contrib import admin
from .models import Holiday


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Admin for Holiday model"""
    list_display = ('title', 'date', 'type', 'teacher', 'created_at')
    list_filter = ('type', 'date', 'teacher')
    search_fields = ('title', 'description', 'teacher__full_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Holiday Details', {
            'fields': ('teacher', 'date', 'title', 'type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
