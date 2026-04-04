"""
Workspace App Admin - Note and File Administration
"""
from django.contrib import admin
from .models import TeacherNote, TeacherFile


@admin.register(TeacherNote)
class TeacherNoteAdmin(admin.ModelAdmin):
    """Admin for TeacherNote model"""
    list_display = ('title', 'teacher', 'is_pinned', 'created_at', 'updated_at')
    list_filter = ('is_pinned', 'teacher', 'created_at')
    search_fields = ('title', 'content', 'teacher__full_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Note Details', {
            'fields': ('teacher', 'title', 'content')
        }),
        ('Options', {
            'fields': ('is_pinned',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeacherFile)
class TeacherFileAdmin(admin.ModelAdmin):
    """Admin for TeacherFile model"""
    list_display = ('title', 'teacher', 'file_type', 'file_size_display', 'uploaded_at')
    list_filter = ('file_type', 'teacher', 'uploaded_at')
    search_fields = ('title', 'description', 'teacher__full_name')
    readonly_fields = ('file_path', 'file_type', 'file_size', 'uploaded_at')
    
    fieldsets = (
        ('File Details', {
            'fields': ('teacher', 'title', 'description')
        }),
        ('File Info', {
            'fields': ('file_path', 'file_type', 'file_size')
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        return obj.file_size_display
    
    file_size_display.short_description = 'File Size'
