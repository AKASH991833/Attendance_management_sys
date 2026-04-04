"""
Super Admin Views - System-wide Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden
from datetime import datetime, timedelta
from apps.accounts.models import Teacher
from apps.students.models import Student, Batch
from apps.students.forms import BatchForm
from apps.attendance.models import AttendanceRecord
from apps.teacher_attendance.models import TeacherAttendance
from apps.timetable.models import TimetableSlot
from .models import SystemLog, SystemConfiguration
from .forms import TeacherCreateForm, TeacherEditForm, SystemLogFilterForm


def is_super_admin(user):
    """Check if user is super admin"""
    return user.is_authenticated and hasattr(user, 'teacher') and user.teacher.is_super_admin


def super_admin_required(view_func):
    """Decorator to require super admin access"""
    return user_passes_test(is_super_admin)(view_func)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_admin_action(admin_user, action, description, target_teacher=None, request=None):
    """Log admin action"""
    SystemLog.objects.create(
        admin_user=admin_user,
        action=action,
        description=description,
        target_teacher=target_teacher,
        ip_address=get_client_ip(request) if request else None
    )


@super_admin_required
def dashboard(request):
    """Super Admin Dashboard"""
    # Overall Statistics
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(user__is_active=True).count()
    inactive_teachers = total_teachers - active_teachers
    super_admins = Teacher.objects.filter(is_super_admin=True).count()

    total_students = Student.objects.count()
    total_batches = Batch.objects.count()

    # Today's stats
    today = timezone.now().date()
    teacher_attendance_today = TeacherAttendance.objects.filter(date=today).count()
    student_attendance_today = AttendanceRecord.objects.filter(date=today).count()

    # Recent teachers
    recent_teachers = Teacher.objects.select_related('user').order_by('-created_at')[:10]

    # Top teachers by students (excluding super admins)
    top_teachers = Teacher.objects.filter(
        is_super_admin=False
    ).annotate(
        student_count=Count('students', distinct=True),
        batch_count=Count('batches', distinct=True)
    ).order_by('-student_count')[:5]

    # Attendance overview (last 7 days)
    from datetime import timedelta
    seven_days_ago = today - timedelta(days=7)

    daily_teacher_attendance = TeacherAttendance.objects.filter(
        date__gte=seven_days_ago,
        date__lte=today
    ).values('date').annotate(
        present=Count('id', filter=Q(status__in=['present', 'late', 'half_day']))
    ).order_by('date')

    context = {
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'inactive_teachers': inactive_teachers,
        'super_admins': super_admins,
        'total_students': total_students,
        'total_batches': total_batches,
        'teacher_attendance_today': teacher_attendance_today,
        'student_attendance_today': student_attendance_today,
        'recent_teachers': recent_teachers,
        'top_teachers': top_teachers,
        'daily_teacher_attendance': list(daily_teacher_attendance),
    }

    return render(request, 'super_admin/dashboard.html', context)


@super_admin_required
def admin_profile(request):
    """Super Admin Profile Page"""
    teacher = request.user.teacher

    # Get statistics for profile
    total_teachers = Teacher.objects.count()
    total_students = Student.objects.count()
    total_batches = Batch.objects.count()
    system_logs_count = SystemLog.objects.count()

    # Get recent activity from system logs
    recent_activity = SystemLog.objects.filter(
        admin_user=request.user
    ).select_related('target_teacher').order_by('-created_at')[:5]

    context = {
        'teacher': teacher,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_batches': total_batches,
        'system_logs_count': system_logs_count,
        'recent_activity': recent_activity,
    }

    if request.method == 'POST':
        # Update profile
        teacher.full_name = request.POST.get('full_name', teacher.full_name)
        teacher.department = request.POST.get('department', teacher.department)
        teacher.phone = request.POST.get('phone', teacher.phone)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            teacher.profile_picture = request.FILES['profile_picture']
        
        teacher.save()

        # Update user email
        user_email = request.POST.get('email')
        if user_email and user_email != request.user.email:
            request.user.email = user_email
            request.user.save()

        # Log the profile update
        SystemLog.objects.create(
            admin_user=request.user,
            action='profile_updated',
            description=f'Updated profile information',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'Profile updated successfully!')
        return redirect('super_admin:admin_profile')

    return render(request, 'super_admin/admin_profile.html', context)


@super_admin_required
def teacher_list(request):
    """List all teachers"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    is_super_admin_filter = request.GET.get('is_super_admin', '')
    show_deleted = request.GET.get('show_deleted', '')

    # By default, only show active teachers (exclude soft-deleted)
    queryset = Teacher.objects.select_related('user').filter(user__is_active=True)

    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(department__icontains=search)
        )

    if status == 'active':
        queryset = queryset.filter(user__is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(user__is_active=False)

    if is_super_admin_filter == 'yes':
        queryset = queryset.filter(is_super_admin=True)
    elif is_super_admin_filter == 'no':
        queryset = queryset.filter(is_super_admin=False)

    # Show deleted teachers if requested
    if show_deleted == 'yes':
        queryset = Teacher.objects.select_related('user').filter(user__is_active=False)

    teachers = queryset.order_by('-created_at')

    context = {
        'teachers': teachers,
        'search': search,
        'status': status,
        'is_super_admin_filter': is_super_admin_filter,
        'show_deleted': show_deleted,
    }

    return render(request, 'super_admin/teacher_list.html', context)


@super_admin_required
def teacher_create(request):
    """Create new teacher"""
    if request.method == 'POST':
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_admin_action(
                request.user,
                'teacher_created',
                f'Created new teacher: {user.teacher.full_name}',
                user.teacher,
                request
            )
            messages.success(request, f"Teacher '{user.teacher.full_name}' created successfully!")
            return redirect('super_admin:teacher_detail', pk=user.teacher.pk)
    else:
        form = TeacherCreateForm()

    context = {
        'form': form,
        'title': 'Create Teacher',
    }

    return render(request, 'super_admin/teacher_form.html', context)


@super_admin_required
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)

    # Teacher's students
    students = teacher.students.all()[:20]
    total_students = teacher.students.count()

    # Teacher's batches
    batches = teacher.batches.all()
    total_batches = batches.count()

    # Teacher's attendance
    teacher_attendance = TeacherAttendance.objects.filter(
        teacher=teacher
    ).order_by('-date')[:10]

    # Student attendance for this teacher's students
    student_attendance = AttendanceRecord.objects.filter(
        teacher=teacher
    ).order_by('-date')[:10]

    # Timetable slots
    timetable_slots = TimetableSlot.objects.filter(
        teacher=teacher
    ).order_by('day_of_week', 'start_time')

    # Statistics
    student_present = AttendanceRecord.objects.filter(
        teacher=teacher,
        status='present'
    ).count()
    student_absent = AttendanceRecord.objects.filter(
        teacher=teacher,
        status='absent'
    ).count()

    teacher_present = TeacherAttendance.objects.filter(
        teacher=teacher,
        status__in=['present', 'late', 'half_day']
    ).count()
    teacher_total = TeacherAttendance.objects.filter(teacher=teacher).count()

    context = {
        'teacher': teacher,
        'students': students,
        'total_students': total_students,
        'batches': batches,
        'total_batches': total_batches,
        'teacher_attendance': teacher_attendance,
        'student_attendance': student_attendance,
        'timetable_slots': timetable_slots,
        'student_present': student_present,
        'student_absent': student_absent,
        'teacher_present': teacher_present,
        'teacher_total': teacher_total,
    }

    log_admin_action(
        request.user,
        'student_viewed',
        f'Viewed details of teacher: {teacher.full_name}',
        teacher,
        request
    )

    return render(request, 'super_admin/teacher_detail.html', context)


@super_admin_required
def teacher_edit(request, pk):
    """Edit teacher profile"""
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        form = TeacherEditForm(request.POST, instance=teacher)
        if form.is_valid():
            user = form.save()
            log_admin_action(
                request.user,
                'teacher_updated',
                f'Updated teacher: {teacher.full_name}',
                teacher,
                request
            )
            messages.success(request, f"Teacher '{teacher.full_name}' updated successfully!")
            return redirect('super_admin:teacher_detail', pk=teacher.pk)
    else:
        form = TeacherEditForm(instance=teacher)

    context = {
        'form': form,
        'teacher': teacher,
        'title': 'Edit Teacher',
    }

    return render(request, 'super_admin/teacher_form.html', context)


@super_admin_required
def teacher_toggle_active(request, pk):
    """Toggle teacher active status"""
    teacher = get_object_or_404(Teacher, pk=pk)

    teacher.user.is_active = not teacher.user.is_active
    teacher.user.save()

    status = 'activated' if teacher.user.is_active else 'deactivated'
    log_admin_action(
        request.user,
        f'teacher_{status}',
        f'{status.capitalize()} teacher: {teacher.full_name}',
        teacher,
        request
    )

    messages.success(request, f"Teacher '{teacher.full_name}' {status} successfully!")
    return redirect('super_admin:teacher_detail', pk=teacher.pk)


@super_admin_required
def teacher_delete(request, pk):
    """Delete teacher (soft delete by deactivating)"""
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        # Soft delete - deactivate user
        teacher.user.is_active = False
        teacher.user.save()

        log_admin_action(
            request.user,
            'teacher_deactivated',
            f'Deleted (deactivated) teacher: {teacher.full_name}',
            teacher,
            request
        )

        messages.success(request, f"Teacher '{teacher.full_name}' deleted successfully!")
        return redirect('super_admin:teacher_list')

    context = {
        'teacher': teacher,
    }

    return render(request, 'super_admin/teacher_delete_confirm.html', context)


@super_admin_required
def teacher_students(request, pk):
    """View all students of a teacher with search, filter, and pagination"""
    from django.core.paginator import Paginator
    
    teacher = get_object_or_404(Teacher, pk=pk)
    
    # Get all students of this teacher
    queryset = teacher.students.select_related('batch', 'teacher').all()
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(full_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    
    # Batch filter
    selected_batch = request.GET.get('batch', '').strip()
    if selected_batch:
        queryset = queryset.filter(batch_id=selected_batch)
    
    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # Order by batch and roll number
    students = queryset.order_by('batch__name', 'roll_number')
    
    # Pagination - 12 students per page
    paginator = Paginator(students, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get batches for filter dropdown
    batches = teacher.batches.all().order_by('name')
    
    # Statistics
    total_students = teacher.students.count()
    active_students = teacher.students.filter(is_active=True).count()
    inactive_students = total_students - active_students
    total_batches = teacher.batches.count()
    
    context = {
        'teacher': teacher,
        'students': page_obj,
        'page_obj': page_obj,
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'total_batches': total_batches,
        'batches': batches,
        'search_query': search_query,
        'selected_batch': selected_batch,
        'status_filter': status_filter,
    }

    return render(request, 'super_admin/teacher_students.html', context)


@super_admin_required
def teacher_timetable(request, pk):
    """View timetable of a teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    timetable_slots = TimetableSlot.objects.filter(
        teacher=teacher
    ).order_by('day_of_week', 'start_time')

    # Group by day
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    timetable_by_day = {}
    for day in days_order:
        timetable_by_day[day] = timetable_slots.filter(day_of_week=day)

    # Calculate statistics
    total_slots = timetable_slots.count()
    days_with_classes = sum(1 for day in days_order if timetable_by_day[day].exists())
    total_batches = teacher.batches.count()
    average_slots_per_day = round(total_slots / days_with_classes, 1) if days_with_classes > 0 else 0

    context = {
        'teacher': teacher,
        'timetable_by_day': timetable_by_day,
        'days_order': days_order,
        'total_slots': total_slots,
        'days_with_classes': days_with_classes,
        'total_batches': total_batches,
        'average_slots_per_day': average_slots_per_day,
    }

    return render(request, 'super_admin/teacher_timetable.html', context)


@super_admin_required
def batch_detail(request, pk):
    """View batch details (read-only for super admin)"""
    batch = get_object_or_404(Batch, pk=pk)
    
    context = {
        'batch': batch,
        'students': batch.students.all(),
        'total_students': batch.students.count(),
        'teacher': batch.teacher,
    }
    
    return render(request, 'super_admin/batch_detail.html', context)


@super_admin_required
def system_logs(request):
    """View system logs"""
    form = SystemLogFilterForm(request.GET or None)

    # Handle clear logs action
    if request.method == 'POST' and request.POST.get('action') == 'clear_logs':
        SystemLog.objects.all().delete()
        messages.success(request, '✅ All logs cleared successfully!')
        return redirect('super_admin:system_logs')

    queryset = SystemLog.objects.select_related('admin_user', 'target_teacher').all()

    if form.is_valid():
        action = form.cleaned_data.get('action')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if action:
            queryset = queryset.filter(action=action)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

    logs = queryset.order_by('-created_at')[:200]

    context = {
        'logs': logs,
        'form': form,
    }

    return render(request, 'super_admin/system_logs.html', context)


@super_admin_required
def mark_teacher_attendance(request):
    """Mark attendance for all teachers - Super Admin can mark who came"""
    # Get selected date or default to today
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_attendance':
            # Mark all selected teachers
            for key, value in request.POST.items():
                if key.startswith('teacher_') and value == 'present':
                    teacher_id = key.split('_')[1]
                    try:
                        teacher = Teacher.objects.get(pk=teacher_id)
                        status = request.POST.get(f'status_{teacher_id}', 'present')
                        notes = request.POST.get(f'notes_{teacher_id}', '')
                        
                        attendance, created = TeacherAttendance.objects.update_or_create(
                            teacher=teacher,
                            date=selected_date,
                            defaults={
                                'status': status,
                                'notes': notes
                            }
                        )
                    except Teacher.DoesNotExist:
                        continue
            
            messages.success(request, f'Teacher attendance marked for {selected_date}!')
            return redirect(f'/admin-panel/teacher-attendance/?date={selected_date}')
        
        elif action == 'mark_all_present':
            # Mark all active teachers as present
            active_teachers = Teacher.objects.filter(user__is_active=True)
            for teacher in active_teachers:
                TeacherAttendance.objects.update_or_create(
                    teacher=teacher,
                    date=selected_date,
                    defaults={'status': 'present'}
                )
            messages.success(request, f'All teachers marked as present for {selected_date}!')
            return redirect(f'/admin-panel/teacher-attendance/?date={selected_date}')
    
    # Get all active teachers
    teachers = Teacher.objects.filter(user__is_active=True).select_related('user').order_by('full_name')
    
    # Get existing attendance for selected date
    attendance_dict = {}
    existing_attendance = TeacherAttendance.objects.filter(date=selected_date)
    for att in existing_attendance:
        attendance_dict[att.teacher_id] = att
    
    # Build teacher list with attendance status
    teacher_list = []
    for teacher in teachers:
        att = attendance_dict.get(teacher.id)
        teacher_list.append({
            'teacher': teacher,
            'attendance': att,
            'status': att.status if att else None,
            'notes': att.notes if att else ''
        })
    
    # Statistics for selected date
    total_teachers = len(teacher_list)
    present_count = sum(1 for t in teacher_list if t['status'] in ['present', 'late', 'half_day'])
    absent_count = sum(1 for t in teacher_list if t['status'] == 'absent')
    leave_count = sum(1 for t in teacher_list if t['status'] == 'on_leave')
    unmarked_count = sum(1 for t in teacher_list if t['status'] is None)
    
    # Previous and next dates for navigation
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)
    is_future = selected_date > timezone.now().date()
    
    context = {
        'teacher_list': teacher_list,
        'selected_date': selected_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'is_future': is_future,
        'total_teachers': total_teachers,
        'present_count': present_count,
        'absent_count': absent_count,
        'leave_count': leave_count,
        'unmarked_count': unmarked_count,
        'present_percentage': round((present_count / total_teachers * 100) if total_teachers > 0 else 0, 1),
    }
    
    return render(request, 'super_admin/mark_teacher_attendance.html', context)


@super_admin_required
def all_students(request):
    """View all students in the system with filtering"""
    from django.core.paginator import Paginator

    search = request.GET.get('search', '')
    batch_id = request.GET.get('batch', '')
    semester = request.GET.get('semester', '')

    queryset = Student.objects.select_related('batch__teacher', 'batch').all()

    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search) |
            Q(roll_number__icontains=search)
        )

    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)

    if semester:
        queryset = queryset.filter(batch__semester=semester)

    students = queryset.order_by('batch__name', 'roll_number')
    batches = Batch.objects.all().order_by('name')
    teachers = Teacher.objects.all()
    
    # Get unique semesters
    semesters = [(str(i), f'Semester {i}') for i in range(1, 9)]

    context = {
        'students': students,
        'batches': batches,
        'teachers': teachers,
        'semesters': semesters,
        'search': search,
        'selected_batch': batch_id,
        'selected_semester': semester,
    }

    return render(request, 'super_admin/all_students.html', context)


@super_admin_required
def all_batches(request):
    """View all batches in the system"""
    batches = Batch.objects.select_related('teacher').order_by('teacher__full_name', 'name')

    context = {
        'batches': batches,
    }

    return render(request, 'super_admin/all_batches.html', context)


@super_admin_required
def export_all_data_excel(request):
    """Export all system data to Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    from datetime import datetime
    
    # Create workbook
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # === Sheet 1: All Teachers ===
    ws_teachers = wb.create_sheet('Teachers')
    teachers_headers = ['ID', 'Name', 'Username', 'Email', 'Department', 'Phone', 'Is Super Admin', 'Status', 'Joined Date', 'Students', 'Batches']
    ws_teachers.append(teachers_headers)
    
    # Style teachers header
    for cell in ws_teachers[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='667eea', end_color='667eea', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')
    
    teachers = Teacher.objects.select_related('user').all()
    for teacher in teachers:
        ws_teachers.append([
            teacher.id,
            teacher.full_name or teacher.user.username,
            teacher.user.username,
            teacher.user.email,
            teacher.department or '-',
            teacher.phone or '-',
            'Yes' if teacher.is_super_admin else 'No',
            'Active' if teacher.user.is_active else 'Inactive',
            teacher.created_at.strftime('%Y-%m-%d'),
            teacher.students.count(),
            teacher.batches.count()
        ])
    
    # === Sheet 2: All Students ===
    ws_students = wb.create_sheet('Students')
    students_headers = ['ID', 'Roll Number', 'Name', 'Email', 'Contact', 'Batch', 'Semester', 'Teacher', 'Status']
    ws_students.append(students_headers)
    
    for cell in ws_students[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='56ab2f', end_color='56ab2f', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')
    
    students = Student.objects.select_related('batch', 'teacher').all()
    for student in students:
        ws_students.append([
            student.id,
            student.roll_number,
            student.full_name,
            student.email or '-',
            student.contact_number or '-',
            student.batch.name,
            f"Sem {student.semester}",
            student.teacher.full_name or student.teacher.user.username,
            'Active' if student.is_active else 'Inactive'
        ])
    
    # === Sheet 3: All Batches ===
    ws_batches = wb.create_sheet('Batches')
    batches_headers = ['ID', 'Batch Name', 'Subject', 'Semester', 'Teacher', 'Students Count', 'Created Date']
    ws_batches.append(batches_headers)
    
    for cell in ws_batches[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='4facfe', end_color='4facfe', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')
    
    batches = Batch.objects.select_related('teacher').all()
    for batch in batches:
        ws_batches.append([
            batch.id,
            batch.name,
            batch.subject or '-',
            f"Semester {batch.semester}",
            batch.teacher.full_name or batch.teacher.user.username,
            batch.students.count(),
            batch.created_at.strftime('%Y-%m-%d')
        ])
    
    # === Sheet 4: Summary ===
    ws_summary = wb.create_sheet('Summary')
    ws_summary.append(['SYSTEM DATA EXPORT SUMMARY'])
    ws_summary.append(['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    ws_summary.append([])
    ws_summary.append(['Metric', 'Count'])
    ws_summary.append(['Total Teachers', Teacher.objects.count()])
    ws_summary.append(['Active Teachers', Teacher.objects.filter(user__is_active=True).count()])
    ws_summary.append(['Total Students', Student.objects.count()])
    ws_summary.append(['Active Students', Student.objects.filter(is_active=True).count()])
    ws_summary.append(['Total Batches', Batch.objects.count()])
    ws_summary.append(['Total Attendance Records', AttendanceRecord.objects.count()])
    
    # Set column widths
    for ws in wb.worksheets:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Create response
    filename = f"edutrack_complete_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    log_admin_action(
        request.user,
        'data_export',
        'Exported all system data to Excel',
        None,
        request
    )
    
    return response
