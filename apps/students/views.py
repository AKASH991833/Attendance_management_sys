"""
Students App Views - Student and Batch Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Student, Batch
from .forms import StudentForm, BatchForm
from apps.accounts.decorators import teacher_login_required


# Batch Views
@teacher_login_required
def batch_list_view(request):
    """
    List all batches for the logged-in teacher.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:teacher_list')
    
    batches = teacher.batches.all()

    context = {
        'batches': batches,
    }
    return render(request, 'batches/list.html', context)


@teacher_login_required
def batch_add_view(request):
    """
    Add a new batch.
    """
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.teacher = request.user.teacher
            batch.save()
            messages.success(request, f'Batch "{batch.name}" created successfully!')
            return redirect('students:batch-list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BatchForm()
    
    return render(request, 'batches/add.html', {'form': form})


@teacher_login_required
def batch_edit_view(request, batch_id):
    """
    Edit an existing batch.
    """
    teacher = request.user.teacher
    batch = get_object_or_404(Batch, pk=batch_id, teacher=teacher)
    
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f'Batch "{batch.name}" updated successfully!')
            return redirect('students:batch-list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BatchForm(instance=batch)
    
    return render(request, 'batches/edit.html', {'form': form, 'batch': batch})


@teacher_login_required
def batch_delete_view(request, batch_id):
    """
    Delete a batch (only if no students are assigned).
    """
    teacher = request.user.teacher
    batch = get_object_or_404(Batch, pk=batch_id, teacher=teacher)
    
    if batch.students.count() > 0:
        messages.error(request, f'Cannot delete batch. {batch.students.count()} student(s) are assigned to this batch.')
        return redirect('students:batch-list')
    
    if request.method == 'POST':
        batch_name = batch.name
        batch.delete()
        messages.success(request, f'Batch "{batch_name}" deleted successfully!')
        return redirect('students:batch-list')
    
    return render(request, 'batches/delete.html', {'batch': batch})


# Student Views
@teacher_login_required
def student_list_view(request):
    """
    List all students for the logged-in teacher.
    Supports advanced filtering by batch, semester, and search by name/roll number.
    """
    teacher = request.user.teacher
    students = teacher.students.select_related('batch').all()

    # Filter by batch
    batch_id = request.GET.get('batch')
    if batch_id:
        students = students.filter(batch_id=batch_id)

    # Filter by semester
    semester = request.GET.get('semester')
    if semester:
        students = students.filter(semester=semester)

    # Search by name or roll number
    search_query = request.GET.get('search')
    search_type = request.GET.get('search_type', 'all')  # all, name, roll
    
    if search_query:
        if search_type == 'name':
            students = students.filter(full_name__icontains=search_query)
        elif search_type == 'roll':
            students = students.filter(roll_number__icontains=search_query)
        else:  # all
            students = students.filter(
                Q(full_name__icontains=search_query) |
                Q(roll_number__icontains=search_query)
            )

    # Pagination
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'batches': teacher.batches.all(),
        'selected_batch': batch_id,
        'selected_semester': semester,
        'search_query': search_query,
        'search_type': search_type,
        'total_students': teacher.students.count(),
        'semesters': [
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
        ],
    }
    return render(request, 'students/list.html', context)


@teacher_login_required
def student_add_view(request):
    """
    Add a new student with auto-generated roll number.
    """
    teacher = request.user.teacher
    preview_roll = None

    if request.method == 'POST':
        form = StudentForm(request.POST, teacher=teacher)
        if form.is_valid():
            student = form.save(commit=False)
            student.teacher = teacher
            # Roll number will be auto-generated in model's save() method
            student.save()
            messages.success(request, f'Student "{student.full_name}" ({student.roll_number}) added successfully!')
            return redirect('students:student-list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(teacher=teacher)
        # Preview roll number for the form
        semester = request.GET.get('semester', '3')
        full_name = request.GET.get('full_name', '')
        if full_name:
            from .models import generate_roll_number
            preview_roll = generate_roll_number(full_name, semester, teacher)

    return render(request, 'students/add.html', {
        'form': form,
        'preview_roll': preview_roll
    })


@teacher_login_required
def student_edit_view(request, student_id):
    """
    Edit an existing student.
    """
    teacher = request.user.teacher
    student = get_object_or_404(Student, pk=student_id, teacher=teacher)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Student "{student.full_name}" updated successfully!')
            return redirect('students:student-list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(instance=student, teacher=teacher)
    
    return render(request, 'students/edit.html', {'form': form, 'student': student})


@teacher_login_required
def student_delete_view(request, student_id):
    """
    Delete a student (cascades to attendance records).
    """
    teacher = request.user.teacher
    student = get_object_or_404(Student, pk=student_id, teacher=teacher)
    
    if request.method == 'POST':
        student_name = student.full_name
        student.delete()
        messages.success(request, f'Student "{student_name}" deleted successfully!')
        return redirect('students:student-list')
    
    return render(request, 'students/delete.html', {'student': student})


@teacher_login_required
def student_detail_view(request, student_id):
    """
    View student details with attendance history.
    """
    teacher = request.user.teacher
    student = get_object_or_404(Student, pk=student_id, teacher=teacher)
    
    context = {
        'student': student,
    }
    return render(request, 'students/detail.html', context)


# API Views
@teacher_login_required
def student_search_api(request):
    """
    API endpoint for searching students.
    Returns JSON results for autocomplete.
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    teacher = request.user.teacher
    students = teacher.students.filter(
        Q(full_name__icontains=query) |
        Q(roll_number__icontains=query)
    )[:10]
    
    results = [
        {
            'id': s.id,
            'name': s.full_name,
            'roll_number': s.roll_number,
            'batch': s.batch.name
        }
        for s in students
    ]
    
    return JsonResponse({'results': results})
