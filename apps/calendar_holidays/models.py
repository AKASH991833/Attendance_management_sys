"""
Calendar & Holidays App Models - Holiday and Event Management
"""
from django.db import models


class Holiday(models.Model):
    """
    Holiday model for tracking holidays, exams, and events.
    Each holiday belongs to a specific teacher (or can be global if teacher is null).
    """
    TYPE_CHOICES = [
        ('holiday', 'Holiday'),
        ('exam', 'Exam'),
        ('event', 'Event'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='holidays', null=True)
    date = models.DateField()
    title = models.CharField(max_length=150)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='holiday')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'holidays'
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']
        unique_together = ['teacher', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['teacher', 'date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.date}"

    @property
    def icon(self):
        """Get icon based on type"""
        icons = {
            'holiday': '🔴',
            'exam': '📝',
            'event': '📅',
        }
        return icons.get(self.type, '📌')

    @property
    def color_class(self):
        """Get CSS class based on type"""
        colors = {
            'holiday': 'holiday',
            'exam': 'exam',
            'event': 'event',
        }
        return colors.get(self.type, 'default')
