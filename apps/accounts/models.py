"""
Accounts App Models - Teacher Profile extending Django User
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Teacher(models.Model):
    """
    Teacher profile model extending Django's User model.
    Each teacher operates in an isolated environment with their own students, batches, etc.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    full_name = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    is_super_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'

    def __str__(self):
        return self.full_name or self.user.username

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/icons/icon-192x192.png'

    @property
    def total_students(self):
        """Get total number of students for this teacher"""
        return self.students.count()

    @property
    def total_batches(self):
        """Get total number of batches for this teacher"""
        return self.batches.count()


@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    """Create Teacher profile when User is created"""
    if created:
        Teacher.objects.create(user=instance, full_name=instance.get_full_name() or instance.username)


@receiver(post_save, sender=User)
def save_teacher_profile(sender, instance, **kwargs):
    """Save Teacher profile when User is saved"""
    if hasattr(instance, 'teacher'):
        instance.teacher.save()
