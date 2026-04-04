"""
Timetable App Admin - Timetable Slot Administration
"""
from django.contrib import admin
from .models import TimetableSlot


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    """Admin for TimetableSlot model"""
    list_display = ('batch', 'teacher', 'day_of_week', 'start_time', 'end_time', 'subject', 'room')
    list_filter = ('day_of_week', 'teacher', 'batch')
    search_fields = ('batch__name', 'subject', 'teacher__full_name', 'room')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Schedule Details', {
            'fields': ('teacher', 'batch', 'day_of_week')
        }),
        ('Time', {
            'fields': ('start_time', 'end_time')
        }),
        ('Class Information', {
            'fields': ('subject', 'room')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
