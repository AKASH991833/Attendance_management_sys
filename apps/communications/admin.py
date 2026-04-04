"""
Communications App Admin - Broadcast Message Administration
"""
from django.contrib import admin
from .models import BroadcastMessage


@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    """Admin for BroadcastMessage model"""
    list_display = ('message_type', 'batch', 'teacher', 'status', 'sent_count', 'failed_count', 'sent_at')
    list_filter = ('message_type', 'status', 'teacher', 'sent_at')
    search_fields = ('message', 'teacher__full_name', 'batch__name')
    readonly_fields = ('sent_count', 'failed_count', 'status', 'sent_at')
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Broadcast Details', {
            'fields': ('teacher', 'batch', 'message_type')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status', 'sent_count', 'failed_count', 'sent_at')
        }),
    )
