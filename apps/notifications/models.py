"""
Notifications App Models - Notification Management
"""
from django.db import models


class Notification(models.Model):
    """
    Notification model for teacher notifications.
    Notifications are created automatically for various events.
    """
    TYPE_CHOICES = [
        ('low_attendance', 'Low Attendance'),
        ('holiday', 'Holiday Reminder'),
        ('reminder', 'Reminder'),
        ('system', 'System'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    related_student = models.ForeignKey('students.Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at', '-is_read']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['teacher', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.teacher.full_name or self.teacher.user.username}"

    @property
    def icon(self):
        """Get icon based on type"""
        icons = {
            'low_attendance': '⚠️',
            'holiday': '📅',
            'reminder': '🔔',
            'system': 'ℹ️',
        }
        return icons.get(self.type, '📌')

    @property
    def color_class(self):
        """Get CSS class based on type"""
        colors = {
            'low_attendance': 'warning',
            'holiday': 'info',
            'reminder': 'primary',
            'system': 'secondary',
        }
        return colors.get(self.type, 'default')
