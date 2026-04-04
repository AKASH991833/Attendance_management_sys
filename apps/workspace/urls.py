"""
Workspace App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'workspace'

urlpatterns = [
    # Notes
    path('notes/', views.notes_view, name='notes'),
    path('notes/add/', views.note_add_view, name='note-add'),
    path('notes/<int:note_id>/edit/', views.note_edit_view, name='note-edit'),
    path('notes/<int:note_id>/delete/', views.note_delete_view, name='note-delete'),
    
    # Files
    path('files/', views.files_view, name='files'),
    path('files/upload/', views.file_upload_view, name='file-upload'),
    path('files/<int:file_id>/download/', views.file_download_view, name='file-download'),
    path('files/<int:file_id>/delete/', views.file_delete_view, name='file-delete'),
]
