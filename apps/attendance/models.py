"""
Attendance App Models - Attendance Record Management
"""
from django.db import models


class AttendanceRecord(models.Model):
    """
    Attendance record model for tracking student attendance.
    Each record represents a student's attendance for a specific date and timetable slot.
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    batch = models.ForeignKey('students.Batch', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    timetable_slot = models.ForeignKey('timetable.TimetableSlot', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.CharField(max_length=255, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['student', 'date', 'timetable_slot']
        ordering = ['-date', 'student__roll_number']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['teacher', 'date']),
            models.Index(fields=['batch', 'date']),
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['teacher', 'student', 'date']),
            models.Index(fields=['teacher', 'batch', 'date']),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"

    @property
    def is_present(self):
        """Check if student was present"""
        return self.status == 'present'

    @property
    def is_absent(self):
        """Check if student was absent"""
        return self.status in ['absent', 'late']
