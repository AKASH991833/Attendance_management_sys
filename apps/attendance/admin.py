"""
Attendance App Admin - Attendance Record Administration
"""
from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin for AttendanceRecord model"""
    list_display = ('student', 'batch', 'teacher', 'date', 'status', 'timetable_slot', 'marked_at')
    list_filter = ('status', 'date', 'batch', 'teacher')
    search_fields = ('student__full_name', 'student__roll_number', 'batch__name')
    readonly_fields = ('marked_at',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('teacher', 'student', 'batch', 'date', 'timetable_slot')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Metadata', {
            'fields': ('marked_at',),
            'classes': ('collapse',)
        }),
    )
