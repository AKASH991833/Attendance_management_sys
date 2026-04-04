"""
Notifications App Admin - Admin Interface for Notifications
"""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    list_display = ['title', 'teacher_name', 'type', 'is_read', 'related_student_name', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'teacher__full_name', 'related_student__full_name']
    readonly_fields = ['created_at']
    list_editable = ['is_read']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('teacher', 'title', 'message', 'type')
        }),
        ('Related Data', {
            'fields': ('related_student', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def teacher_name(self, obj):
        """Get the teacher's name."""
        return obj.teacher.full_name or obj.teacher.user.email
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__full_name'
    
    def related_student_name(self, obj):
        """Get the related student's name."""
        if obj.related_student:
            return obj.related_student.full_name
        return '-'
    related_student_name.short_description = 'Student'
    related_student_name.admin_order_field = 'related_student__full_name'
