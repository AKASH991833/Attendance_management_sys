"""
Workspace App Views - Teacher Notes and Files Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.http import FileResponse
from django.db import transaction
import os
import uuid
import mimetypes
from datetime import datetime
from .models import TeacherNote, TeacherFile
from .forms import TeacherNoteForm, TeacherFileForm
from apps.accounts.decorators import teacher_login_required, ajax_required

# File Upload Security Settings
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_upload(uploaded_file):
    """
    Validate uploaded file for security.
    Returns (is_valid, error_message)
    """
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'
    
    # Get file extension
    ext = os.path.splitext(uploaded_file.name)[1].lower()[1:]
    
    # Check extension
    if ext not in ALLOWED_EXTENSIONS:
        return False, f'File type .{ext} not allowed. Allowed: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, TXT'
    
    return True, None


# Note Views
@teacher_login_required
def notes_view(request):
    """
    List all notes for the logged-in teacher.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')

    # Get all notes, pinned first
    notes = TeacherNote.objects.filter(teacher=teacher)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    context = {
        'notes': notes,
        'search_query': search_query,
    }
    return render(request, 'workspace/notes.html', context)


@teacher_login_required
def note_add_view(request):
    """
    Add a new note.
    """
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = TeacherNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.teacher = teacher
            note.save()
            messages.success(request, f'Note "{note.title}" created successfully!')
            return redirect('workspace:notes')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherNoteForm()
    
    return render(request, 'workspace/note_form.html', {'form': form, 'action': 'add'})


@teacher_login_required
def note_edit_view(request, note_id):
    """
    Edit an existing note.
    """
    teacher = request.user.teacher
    note = get_object_or_404(TeacherNote, pk=note_id, teacher=teacher)
    
    if request.method == 'POST':
        form = TeacherNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Note "{note.title}" updated successfully!')
            return redirect('workspace:notes')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherNoteForm(instance=note)
    
    return render(request, 'workspace/note_form.html', {'form': form, 'note': note, 'action': 'edit'})


@teacher_login_required
def note_delete_view(request, note_id):
    """
    Delete a note.
    """
    teacher = request.user.teacher
    note = get_object_or_404(TeacherNote, pk=note_id, teacher=teacher)
    
    if request.method == 'POST':
        note_title = note.title
        note.delete()
        messages.success(request, f'Note "{note_title}" deleted successfully!')
        return redirect('workspace:notes')
    
    return render(request, 'workspace/note_delete.html', {'note': note})


# File Views
@teacher_login_required
def files_view(request):
    """
    List all files for the logged-in teacher.
    """
    teacher = request.user.teacher
    files = TeacherFile.objects.filter(teacher=teacher)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        files = files.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'files': files,
        'search_query': search_query,
    }
    return render(request, 'workspace/files.html', context)


@teacher_login_required
@transaction.atomic
def file_upload_view(request):
    """
    Upload a new file with security validation.
    """
    teacher = request.user.teacher

    if request.method == 'POST':
        form = TeacherFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES.get('file')
            
            if not uploaded_file:
                messages.error(request, 'No file selected')
                return render(request, 'workspace/file_upload.html', {'form': form})
            
            # Validate file
            is_valid, error_message = validate_file_upload(uploaded_file)
            if not is_valid:
                messages.error(request, f'Upload failed: {error_message}')
                return render(request, 'workspace/file_upload.html', {'form': form})
            
            file_obj = form.save(commit=False)
            file_obj.teacher = teacher

            # Generate unique file path
            ext = uploaded_file.name.split('.')[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            folder = os.path.join(settings.MEDIA_ROOT, 'workspace_files', str(teacher.id))

            # Create folder if it doesn't exist
            os.makedirs(folder, exist_ok=True)

            # Save file
            file_path = os.path.join(folder, filename)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            file_obj.file_path = file_path
            file_obj.file_size = uploaded_file.size

            # Determine file type
            type_map = {
                'pdf': 'pdf',
                'docx': 'docx',
                'doc': 'doc',
                'xlsx': 'xlsx',
                'xls': 'xls',
                'png': 'png',
                'jpg': 'jpg',
                'jpeg': 'jpeg',
                'txt': 'txt',
            }
            file_obj.file_type = type_map.get(ext, 'other')

            file_obj.save()
            
            messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
            return redirect('workspace:files')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherFileForm()

    return render(request, 'workspace/file_upload.html', {
        'form': form,
        'max_size_mb': MAX_FILE_SIZE // (1024 * 1024),
        'allowed_types': 'PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, TXT'
    })


@teacher_login_required
def file_download_view(request, file_id):
    """
    Download a file.
    """
    teacher = request.user.teacher
    file_obj = get_object_or_404(TeacherFile, pk=file_id, teacher=teacher)
    
    if os.path.exists(file_obj.file_path):
        return FileResponse(
            open(file_obj.file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_obj.file_path)
        )
    else:
        messages.error(request, 'File not found on server.')
        return redirect('workspace:files')


@teacher_login_required
def file_delete_view(request, file_id):
    """
    Delete a file (removes from disk and database).
    """
    teacher = request.user.teacher
    file_obj = get_object_or_404(TeacherFile, pk=file_id, teacher=teacher)
    
    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.delete()  # This also deletes the actual file
        messages.success(request, f'File "{file_title}" deleted successfully!')
        return redirect('workspace:files')
    
    return render(request, 'workspace/file_delete.html', {'file': file_obj})
