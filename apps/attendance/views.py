"""
Attendance App Views - Attendance Marking and History
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
import json
from .models import AttendanceRecord
from .forms import AttendanceMarkForm, AttendanceHistoryFilterForm
from apps.students.models import Student, Batch
from apps.accounts.decorators import teacher_login_required, ajax_required


@teacher_login_required
def mark_attendance_view(request):
    """
    Monthly Attendance Grid View - Excel-like interface (DEFAULT)
    This is the main attendance page now
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')
    
    today = timezone.now().date()

    # Get filter parameters
    selected_month = request.GET.get('month', today.strftime('%Y-%m'))
    selected_batch_id = request.GET.get('batch')
    selected_semester = request.GET.get('semester', '3')  # Default Sem 3

    # Auto-set current month if not provided
    if not selected_month:
        selected_month = today.strftime('%Y-%m')

    # Parse month
    try:
        month_date = datetime.strptime(selected_month + '-01', '%Y-%m-%d').date()
        year = month_date.year
        month = month_date.month
        month_name = month_date.strftime('%B %Y')
        days_in_month = monthrange(year, month)[1]
    except (ValueError, TypeError):
        month_date = today.replace(day=1)
        year = today.year
        month = today.month
        month_name = today.strftime('%B %Y')
        days_in_month = monthrange(year, month)[1]

    # Get batches and slots
    batches = teacher.batches.all().order_by('name')
    slots = []
    if selected_batch_id:
        from apps.timetable.models import TimetableSlot
        slots = TimetableSlot.objects.filter(
            teacher=teacher,
            batch_id=selected_batch_id
        ).order_by('day_of_week', 'start_time')

    # Get students if batch selected
    students = []
    if selected_batch_id:
        try:
            batch = Batch.objects.get(pk=selected_batch_id, teacher=teacher)
            students = list(batch.students.filter(is_active=True).order_by('roll_number'))
        except Batch.DoesNotExist:
            pass

    # Generate date list for the month
    date_list = []
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day).date()
        date_list.append({
            'date': date_obj,
            'day': date_obj.strftime('%d'),
            'weekday': date_obj.strftime('%a'),
            'is_future': date_obj > today,
            'is_today': date_obj == today,
            'is_sunday': date_obj.weekday() == 6  # Sunday is 6
        })

    context = {
        'selected_month': selected_month,
        'selected_batch_id': selected_batch_id,
        'selected_semester': selected_semester,
        'month_name': month_name,
        'year': year,
        'month': month,
        'days_in_month': days_in_month,
        'date_list': date_list,
        'students': students,
        'batches': batches,
        'slots': slots,
        'today': today,
        'semesters': [
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
        ],
        'page_type': 'monthly'
    }

    return render(request, 'attendance/mark.html', context)


@teacher_login_required
@ajax_required
@transaction.atomic
def save_attendance_api(request):
    """
    API endpoint to save attendance records.
    Expects JSON payload with student statuses.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    teacher = request.user.teacher
    date_str = data.get('date')
    batch_id = data.get('batch_id')
    slot_id = data.get('slot_id')
    students_data = data.get('students', [])
    
    # Validate required fields
    if not date_str or not batch_id or not students_data:
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    # Parse date
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    # RULE: Do NOT allow marking attendance on SUNDAYS
    if date.weekday() == 6:  # Sunday is 6 (Monday=0, Sunday=6)
        return JsonResponse({'error': 'Cannot mark attendance on Sunday'}, status=400)

    # Validate batch
    try:
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
    except Batch.DoesNotExist:
        return JsonResponse({'error': 'Invalid request data'}, status=404)

    # Validate slot if provided
    slot = None
    if slot_id:
        try:
            from apps.timetable.models import TimetableSlot
            slot = TimetableSlot.objects.get(pk=slot_id, teacher=teacher, batch=batch)
        except (TimetableSlot.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid request data'}, status=400)
    
    # Process each student's attendance
    saved_count = 0
    low_attendance_notifications = []
    
    for student_data in students_data:
        student_id = student_data.get('student_id')
        status = student_data.get('status', 'present')
        notes = student_data.get('notes', '')
        
        if not student_id:
            continue
        
        try:
            student = Student.objects.get(pk=student_id, teacher=teacher)
        except Student.DoesNotExist:
            continue
        
        # Validate status
        valid_statuses = ['present', 'absent', 'late', 'excused']
        if status not in valid_statuses:
            status = 'present'
        
        # Create or update attendance record
        record, created = AttendanceRecord.objects.update_or_create(
            teacher=teacher,
            student=student,
            batch=batch,
            date=date,
            timetable_slot=slot,
            defaults={
                'status': status,
                'notes': notes[:255]  # Truncate notes if too long
            }
        )
        saved_count += 1
        
        # Check for low attendance and create notification
        if status in ['absent', 'late']:
            total_classes = student.attendance_records.count()
            if total_classes > 0:
                present_count = student.attendance_records.filter(status='present').count()
                percentage = (present_count / total_classes) * 100
                if percentage < 75:
                    low_attendance_notifications.append({
                        'student': student,
                        'percentage': round(percentage, 1)
                    })
    
    # Create notifications for low attendance students
    for notif_data in low_attendance_notifications:
        student = notif_data['student']
        percentage = notif_data['percentage']
        from apps.notifications.models import Notification
        Notification.objects.create(
            teacher=teacher,
            title=f'Low Attendance: {student.full_name}',
            message=f'{student.full_name} (Roll: {student.roll_number}) has attendance {percentage}% in {batch.name}.',
            type='low_attendance',
            related_student=student
        )
    
    return JsonResponse({
        'success': True,
        'saved_count': saved_count,
        'message': f'Attendance saved for {saved_count} student(s)'
    })


@teacher_login_required
@ajax_required
def check_attendance_api(request):
    """
    API endpoint to check if attendance is already marked for a date/batch/slot.
    """
    teacher = request.user.teacher
    date_str = request.GET.get('date')
    batch_id = request.GET.get('batch_id')
    slot_id = request.GET.get('slot_id')
    
    if not date_str or not batch_id:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
    except (ValueError, Batch.DoesNotExist):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    # Check if attendance exists
    records = AttendanceRecord.objects.filter(
        teacher=teacher,
        batch=batch,
        date=date
    )
    
    if slot_id:
        try:
            from apps.timetable.models import TimetableSlot
            slot = TimetableSlot.objects.get(pk=slot_id, teacher=teacher)
            records = records.filter(timetable_slot=slot)
        except (TimetableSlot.DoesNotExist, ValueError):
            pass
    
    exists = records.exists()
    
    return JsonResponse({
        'exists': exists,
        'count': records.count()
    })


@teacher_login_required
def attendance_history_view(request):
    """
    View attendance history with filters.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')
    
    # Initialize filter form
    form = AttendanceHistoryFilterForm(teacher=teacher, data=request.GET or None)
    
    # Base queryset
    records = AttendanceRecord.objects.filter(teacher=teacher).select_related('student', 'batch', 'timetable_slot')
    
    # Apply filters
    if form.is_valid():
        batch_id = form.cleaned_data.get('batch')
        from_date = form.cleaned_data.get('from_date')
        to_date = form.cleaned_data.get('to_date')
        student_name = form.cleaned_data.get('student_name')
        
        if batch_id:
            records = records.filter(batch=batch_id)
        if from_date:
            records = records.filter(date__gte=from_date)
        if to_date:
            records = records.filter(date__lte=to_date)
        if student_name:
            records = records.filter(student__full_name__icontains=student_name)
    
    # Group by date and batch for summary view
    summary = records.values('date', 'batch', 'batch__name').annotate(
        present_count=Count('id', filter=Q(status='present')),
        absent_count=Count('id', filter=Q(status__in=['absent', 'late']))
    ).order_by('-date', 'batch__name')
    
    # Pagination
    paginator = Paginator(summary, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    return render(request, 'attendance/history.html', context)


@teacher_login_required
def student_attendance_detail_view(request, student_id):
    """
    View detailed attendance for a specific student.
    """
    teacher = request.user.teacher
    student = get_object_or_404(Student, pk=student_id, teacher=teacher)
    
    # Get attendance records
    records = student.attendance_records.select_related('batch', 'timetable_slot').order_by('-date')
    
    # Pagination
    paginator = Paginator(records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats
    total_classes = student.attendance_records.count()
    present_count = student.attendance_records.filter(status='present').count()
    absent_count = student.attendance_records.filter(status__in=['absent', 'late']).count()
    attendance_percentage = student.attendance_percentage
    
    # Get monthly data for heatmap
    from datetime import date
    today = date.today()
    first_day = today.replace(day=1)
    monthly_records = student.attendance_records.filter(
        date__year=today.year,
        date__month=today.month
    )
    
    context = {
        'student': student,
        'page_obj': page_obj,
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'monthly_records': monthly_records,
        'current_month': today.strftime('%B %Y'),
    }
    return render(request, 'attendance/student_detail.html', context)


@teacher_login_required
@ajax_required
def monthly_attendance_fetch_api(request):
    """
    API to fetch monthly attendance data for a batch
    GET /api/attendance/monthly/?batch_id=&month=
    """
    teacher = request.user.teacher
    
    batch_id = request.GET.get('batch_id')
    month = request.GET.get('month')
    
    # Handle empty string values
    if batch_id == '' or batch_id == 'null':
        batch_id = None
    
    if not batch_id or not month:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    # Parse month
    try:
        month_date = datetime.strptime(month + '-01', '%Y-%m-%d').date()
        year = month_date.year
        month_num = month_date.month
        days_in_month = monthrange(year, month_num)[1]
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid month format'}, status=400)
    
    # Validate batch
    try:
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
    except Batch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    
    # Get students
    students = list(batch.students.filter(is_active=True).order_by('roll_number').values(
        'id', 'roll_number', 'full_name'
    ))
    
    # Get attendance records for the month
    records = AttendanceRecord.objects.filter(
        teacher=teacher,
        batch=batch,
        date__year=year,
        date__month=month_num
    )
    
    # Build attendance data
    attendance_data = {}
    for record in records:
        student_id = record.student_id
        date_str = record.date.strftime('%Y-%m-%d')
        
        if student_id not in attendance_data:
            attendance_data[student_id] = {}
        
        attendance_data[student_id][date_str] = {
            'status': record.status,
            'notes': record.notes
        }
    
    # Generate date list
    date_list = []
    today = timezone.now().date()
    for day in range(1, days_in_month + 1):
        try:
            date_obj = datetime(year, month_num, day).date()
            date_list.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'day': date_obj.strftime('%d'),
                'weekday': date_obj.strftime('%a'),
                'is_future': date_obj > today,
                'is_today': date_obj == today,
                'is_sunday': date_obj.weekday() == 6  # Sunday is 6
            })
        except:
            pass
    
    return JsonResponse({
        'success': True,
        'students': students,
        'attendance': attendance_data,
        'dates': date_list,
        'month_name': month_date.strftime('%B %Y'),
        'days_in_month': days_in_month
    })


@teacher_login_required
@ajax_required
@transaction.atomic
def monthly_attendance_save_api(request):
    """
    API to save monthly attendance
    POST /api/attendance/monthly/save/

    Payload:
    {
        "batch_id": X,
        "month": "2026-03",
        "data": [
            {
                "student_id": 1,
                "dates": {
                    "2026-03-01": "present",
                    "2026-03-02": "absent"
                }
            }
        ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    teacher = request.user.teacher
    batch_id = data.get('batch_id')
    month_str = data.get('month')
    students_data = data.get('data', [])

    # Handle empty/null values
    if batch_id == '' or batch_id == 'null':
        batch_id = None

    # Validate required fields
    if not batch_id or not month_str or not students_data:
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    # Parse month
    try:
        month_date = datetime.strptime(month_str + '-01', '%Y-%m-%d').date()
        year = month_date.year
        month_num = month_date.month
        days_in_month = monthrange(year, month_num)[1]
        today = timezone.now().date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid month format'}, status=400)
    
    # Validate batch
    try:
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
    except Batch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)

    # Process each student's attendance
    saved_count = 0
    updated_count = 0
    errors = []

    for student_entry in students_data:
        student_id = student_entry.get('student_id')
        dates_data = student_entry.get('dates', {})

        if not student_id or not dates_data:
            continue

        try:
            student = Student.objects.get(pk=student_id, teacher=teacher)
        except Student.DoesNotExist:
            errors.append(f'Student {student_id} not found')
            continue

        # Process each date
        for date_str, status in dates_data.items():
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # RULE 1: Do NOT allow future dates
                if attendance_date > today:
                    continue

                # RULE 2: Only allow dates from the selected month
                if attendance_date.month != month_num or attendance_date.year != year:
                    continue

                # RULE 3: Do NOT allow marking attendance on SUNDAYS
                if attendance_date.weekday() == 6:  # Sunday is 6 (Monday=0, Sunday=6)
                    errors.append(f'Cannot mark attendance on Sunday ({date_str})')
                    continue

                # RULE 4: Validate status
                valid_statuses = ['present', 'absent', 'late', 'excused']
                if status not in valid_statuses:
                    status = 'present'

                # RULE 5: If record exists → update, If not → create
                record, created = AttendanceRecord.objects.update_or_create(
                    teacher=teacher,
                    student=student,
                    batch=batch,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'notes': ''
                    }
                )

                if created:
                    saved_count += 1
                else:
                    updated_count += 1
                    
            except (ValueError, TypeError) as e:
                errors.append(f'Invalid date {date_str} for student {student_id}')
                continue
    
    return JsonResponse({
        'success': True,
        'saved_count': saved_count,
        'updated_count': updated_count,
        'total_processed': saved_count + updated_count,
        'errors': errors,
        'message': f'Saved {saved_count} new, updated {updated_count} existing records'
    })


@teacher_login_required
@ajax_required
def mark_day_attendance_api(request):
    """
    API to mark attendance for all students for a specific day
    POST /api/attendance/mark-day/
    
    Payload:
    {
        "batch_id": X,
        "date": "2026-03-15",
        "status": "present",  // or "absent"
        "slot_id": X (optional)
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    teacher = request.user.teacher
    batch_id = data.get('batch_id')
    date_str = data.get('date')
    status = data.get('status', 'present')
    slot_id = data.get('slot_id')
    
    # Validate
    if not batch_id or not date_str:
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    # Parse date
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = timezone.now().date()
        
        # Do not allow future dates
        if attendance_date > today:
            return JsonResponse({'error': 'Cannot mark attendance for future dates'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Validate batch
    try:
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
    except Batch.DoesNotExist:
        return JsonResponse({'error': 'Batch not found'}, status=404)
    
    # Validate slot
    slot = None
    if slot_id:
        try:
            from apps.timetable.models import TimetableSlot
            slot = TimetableSlot.objects.get(pk=slot_id, teacher=teacher, batch=batch)
        except (TimetableSlot.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid slot'}, status=400)
    
    # Get all active students in batch
    students = batch.students.filter(is_active=True)
    
    # Mark attendance for all
    saved_count = 0
    for student in students:
        record, created = AttendanceRecord.objects.update_or_create(
            teacher=teacher,
            student=student,
            batch=batch,
            date=attendance_date,
            timetable_slot=slot,
            defaults={
                'status': status,
                'notes': ''
            }
        )
        saved_count += 1
    
    return JsonResponse({
        'success': True,
        'saved_count': saved_count,
        'message': f'Marked {status} for {saved_count} students on {date_str}'
    })
