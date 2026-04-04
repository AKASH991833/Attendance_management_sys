"""
Students App Admin - Student and Batch Administration
"""
from django.contrib import admin
from .models import Batch, Student


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Admin for Batch model"""
    list_display = ('name', 'semester', 'subject', 'teacher', 'student_count', 'created_at')
    list_filter = ('semester', 'teacher', 'created_at')
    search_fields = ('name', 'subject', 'teacher__full_name')
    readonly_fields = ('created_at',)

    def student_count(self, obj):
        return obj.students.count()

    student_count.short_description = 'Students'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin for Student model"""
    list_display = ('roll_number', 'full_name', 'semester', 'batch', 'teacher', 'contact_number', 'is_active')
    list_filter = ('semester', 'batch', 'teacher', 'is_active')
    search_fields = ('full_name', 'roll_number', 'email', 'contact_number')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('full_name', 'roll_number', 'email')
        }),
        ('Academic Details', {
            'fields': ('teacher', 'batch', 'semester')
        }),
        ('Contact Information', {
            'fields': ('contact_number',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
