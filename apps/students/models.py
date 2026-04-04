"""
Students App Models - Student and Batch Management
"""
from django.db import models
from django.db.models import Count, Q
import re


def generate_roll_number(name, semester, teacher, offset=0):
    """
    Generate unique roll number based on student name.
    Format: First 2 letters of name + sequential number
    Example: Akash -> AK001, AK002, Aman -> AM001
    """
    # Extract first 2 letters from name (take first alpha characters)
    alpha_chars = [c for c in name.upper() if c.isalpha()]
    if len(alpha_chars) >= 2:
        prefix = alpha_chars[0] + alpha_chars[1]
    elif len(alpha_chars) == 1:
        prefix = alpha_chars[0] + 'A'
    else:
        prefix = 'ST'  # Default for non-alpha names
    
    # Get count of students with this prefix in this semester
    count = Student.objects.filter(
        teacher=teacher,
        semester=semester,
        roll_number__startswith=prefix
    ).count()
    
    # Next number is count + 1 + offset
    next_number = count + 1 + offset
    
    # Format: AK001, AK002, etc.
    roll_number = f'{prefix}{next_number:03d}'
    
    return roll_number


class Batch(models.Model):
    """
    Batch model representing a class/section that a teacher manages.
    Each batch belongs to a specific teacher and has a semester and subject.
    """
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
    ]

    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=50)  # e.g., "Batch A", "Sem 3-2024"
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, default='3')
    subject = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'batches'  # Explicit table name
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        ordering = ['name']
        indexes = [
            models.Index(fields=['teacher', 'semester']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} - Sem {self.semester}"

    @property
    def student_count(self):
        """Get number of students in this batch"""
        return self.students.count()

    @property
    def can_delete(self):
        """Check if batch can be deleted (no students assigned)"""
        return self.students.count() == 0


class Student(models.Model):
    """
    Student model representing a student enrolled in a batch.
    Each student belongs to a teacher and a batch.
    Roll number is auto-generated based on name (e.g., Akash -> AK001).
    """
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
    ]

    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='students')
    batch = models.ForeignKey('Batch', on_delete=models.CASCADE, related_name='students')
    full_name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=20, editable=True)  # Can be edited
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, default='3')
    contact_number = models.CharField(max_length=15)  # WhatsApp number
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['roll_number']
        unique_together = ['teacher', 'roll_number']  # Roll number unique per teacher
        indexes = [
            models.Index(fields=['teacher', 'semester']),
            models.Index(fields=['batch', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['teacher', 'roll_number']),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate roll number if not set"""
        if not self.roll_number and self.full_name:
            # Get next roll number for this semester
            semester_count = Student.objects.filter(
                teacher=self.teacher,
                semester=self.semester
            ).count()
            self.roll_number = f'{self.semester}{semester_count + 1:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.roll_number} - {self.full_name}"

    @property
    def attendance_percentage(self):
        """Calculate student's overall attendance percentage"""
        total_classes = self.attendance_records.count()
        if total_classes == 0:
            return 100.0
        present_count = self.attendance_records.filter(status='present').count()
        return round((present_count / total_classes) * 100, 1)

    @property
    def total_classes(self):
        """Get total number of attendance records"""
        return self.attendance_records.count()

    @property
    def present_count(self):
        """Get count of present days"""
        return self.attendance_records.filter(status='present').count()

    @property
    def absent_count(self):
        """Get count of absent days"""
        return self.attendance_records.filter(status__in=['absent', 'late']).count()

    def get_attendance_for_date_range(self, from_date, to_date):
        """Get attendance stats for a specific date range"""
        records = self.attendance_records.filter(date__range=[from_date, to_date])
        total = records.count()
        if total == 0:
            return {'total': 0, 'present': 0, 'absent': 0, 'percentage': 100.0}
        present = records.filter(status='present').count()
        absent = records.filter(status__in=['absent', 'late']).count()
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': round((present / total) * 100, 1)
        }
