"""
Teacher Attendance App Models - Teacher Attendance Tracking
"""
from django.db import models
from django.utils import timezone


class TeacherAttendance(models.Model):
    """
    Attendance record model for tracking teacher attendance.
    Each record represents a teacher's attendance for a specific date.
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('on_leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ]

    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, help_text="Optional notes for this attendance")
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teacher_attendance'
        verbose_name = 'Teacher Attendance'
        verbose_name_plural = 'Teacher Attendances'
        unique_together = ['teacher', 'date']
        ordering = ['-date', 'teacher__user__username']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['teacher', 'date']),
            models.Index(fields=['status', 'date']),
        ]

    def __str__(self):
        return f"{self.teacher.full_name or self.teacher.user.username} - {self.date} - {self.status}"

    @property
    def is_present(self):
        """Check if teacher was present"""
        return self.status in ['present', 'late', 'half_day']

    @property
    def is_absent(self):
        """Check if teacher was absent"""
        return self.status == 'absent'

    @property
    def is_on_leave(self):
        """Check if teacher is on leave"""
        return self.status == 'on_leave'

    def mark_check_in(self):
        """Mark check-in time"""
        if not self.check_in_time:
            self.check_in_time = timezone.now().time()
            self.save()

    def mark_check_out(self):
        """Mark check-out time"""
        if not self.check_out_time:
            self.check_out_time = timezone.now().time()
            self.save()
