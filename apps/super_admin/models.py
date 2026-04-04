"""
Super Admin App Models - System-wide Management
"""
from django.db import models
from django.utils import timezone


class SystemLog(models.Model):
    """
    Log model for tracking system-wide activities by super admin.
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('teacher_created', 'Teacher Created'),
        ('teacher_updated', 'Teacher Updated'),
        ('teacher_deleted', 'Teacher Deleted'),
        ('teacher_activated', 'Teacher Activated'),
        ('teacher_deactivated', 'Teacher Deactivated'),
        ('student_viewed', 'Student Viewed'),
        ('batch_viewed', 'Batch Viewed'),
        ('report_generated', 'Report Generated'),
        ('system_config', 'System Configuration'),
        ('other', 'Other'),
    ]

    admin_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='admin_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.CharField(max_length=500)
    target_teacher = models.ForeignKey('accounts.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_logs'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.admin_user.username} - {self.action} - {self.created_at}"


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings managed by super admin.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='config_updates')

    class Meta:
        db_table = 'system_configurations'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'

    def __str__(self):
        return self.key
