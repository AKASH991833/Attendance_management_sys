"""
Workspace App Models - Teacher Notes and Files
"""
from django.db import models
import os


class TeacherNote(models.Model):
    """
    Teacher note model for personal workspace notes.
    """
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teacher_notes'
        verbose_name = 'Teacher Note'
        verbose_name_plural = 'Teacher Notes'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    @property
    def preview(self):
        """Get first 100 characters of content"""
        if len(self.content) > 100:
            return self.content[:100] + '...'
        return self.content


class TeacherFile(models.Model):
    """
    Teacher file model for personal workspace files.
    """
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('doc', 'Word Document'),
        ('xlsx', 'Excel Spreadsheet'),
        ('xls', 'Excel Spreadsheet'),
        ('png', 'PNG Image'),
        ('jpg', 'JPEG Image'),
        ('jpeg', 'JPEG Image'),
        ('gif', 'GIF Image'),
        ('txt', 'Text File'),
        ('other', 'Other'),
    ]
    
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.IntegerField(help_text='File size in bytes')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_files'
        verbose_name = 'Teacher File'
        verbose_name_plural = 'Teacher Files'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def file_size_display(self):
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def icon_class(self):
        """Get icon class based on file type"""
        icons = {
            'pdf': 'fa-file-pdf',
            'docx': 'fa-file-word',
            'doc': 'fa-file-word',
            'xlsx': 'fa-file-excel',
            'xls': 'fa-file-excel',
            'png': 'fa-file-image',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'gif': 'fa-file-image',
            'txt': 'fa-file-alt',
        }
        return icons.get(self.file_type, 'fa-file')

    def delete(self, *args, **kwargs):
        """Delete the actual file when the record is deleted"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except Exception as e:
                print(f"Error deleting file {self.file_path}: {e}")
        super().delete(*args, **kwargs)
