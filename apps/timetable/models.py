"""
Timetable App Models - Timetable Slot Management
"""
from django.db import models


class TimetableSlot(models.Model):
    """
    Timetable slot model representing a class session.
    Each slot defines a specific day, time, batch, and subject.
    """
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='timetable_slots')
    batch = models.ForeignKey('students.Batch', on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=100)
    room = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'timetable_slots'
        verbose_name = 'Timetable Slot'
        verbose_name_plural = 'Timetable Slots'
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['teacher', 'day_of_week']),
            models.Index(fields=['batch', 'day_of_week']),
        ]

    def __str__(self):
        return f"{self.batch.name} - {self.day_of_week} {self.start_time}-{self.end_time}"

    @property
    def duration_minutes(self):
        """Calculate slot duration in minutes"""
        start = self.start_time
        end = self.end_time
        return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)

    def has_time_conflict(self, other_slot):
        """
        Check if this slot has a time conflict with another slot on the same day.
        Returns True if there's an overlap.
        """
        if self.day_of_week != other_slot.day_of_week:
            return False
        
        # Check for time overlap
        # Two slots overlap if: start1 < end2 AND end1 > start2
        return self.start_time < other_slot.end_time and self.end_time > other_slot.start_time

    def clean(self):
        """
        Validate that there are no time conflicts with other slots for this teacher.
        """
        from django.core.exceptions import ValidationError

        # Skip validation if teacher is not set yet (e.g., during form validation)
        if not self.teacher_id:
            return

        # Check for conflicts with other slots of the same teacher on the same day
        conflicts = TimetableSlot.objects.filter(
            teacher=self.teacher,
            day_of_week=self.day_of_week
        ).exclude(pk=self.pk)

        for slot in conflicts:
            if self.has_time_conflict(slot):
                raise ValidationError(
                    f"Time conflict with existing slot: {slot.batch.name} on {slot.day_of_week} "
                    f"from {slot.start_time} to {slot.end_time}"
                )
