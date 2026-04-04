"""
Communications App Models - WhatsApp Broadcast Management
"""
from django.db import models


class BroadcastMessage(models.Model):
    """
    Broadcast message model for tracking WhatsApp broadcasts.
    Each broadcast is sent to students in a specific batch or all batches.
    """
    MESSAGE_TYPE_CHOICES = [
        ('holiday', 'Holiday Notice'),
        ('attendance_alert', 'Attendance Alert'),
        ('announcement', 'General Announcement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='broadcast_messages')
    batch = models.ForeignKey('students.Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='broadcast_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    message = models.TextField()
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'broadcast_messages'
        verbose_name = 'Broadcast Message'
        verbose_name_plural = 'Broadcast Messages'
        ordering = ['-sent_at']

    def __str__(self):
        batch_name = self.batch.name if self.batch else 'All Batches'
        return f"{self.get_message_type_display()} - {batch_name} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def total_recipients(self):
        """Get total number of recipients"""
        if self.batch:
            return self.batch.students.filter(is_active=True).count()
        else:
            from apps.accounts.models import Teacher
            teacher = self.teacher
            total = 0
            for batch in teacher.batches.all():
                total += batch.students.filter(is_active=True).count()
            return total

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        total = self.sent_count + self.failed_count
        if total == 0:
            return 0
        return round((self.sent_count / total) * 100, 1)
