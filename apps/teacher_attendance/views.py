"""
Teacher Attendance Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from .models import TeacherAttendance
from .forms import TeacherAttendanceForm, TeacherAttendanceBulkForm
from apps.accounts.models import Teacher


@login_required
def mark_attendance(request):
    """Mark teacher attendance for a specific date"""
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = TeacherAttendanceForm(request.POST, teacher=teacher)
        if form.is_valid():
            # Check if attendance already exists for this date
            existing = TeacherAttendance.objects.filter(
                teacher=teacher,
                date=form.cleaned_data['date']
            ).first()
            
            if existing:
                # Update existing record
                existing.status = form.cleaned_data['status']
                existing.notes = form.cleaned_data['notes']
                existing.save()
                messages.success(request, f"Attendance updated for {form.cleaned_data['date']}!")
            else:
                # Create new record
                attendance = form.save(commit=False)
                attendance.teacher = teacher
                if form.cleaned_data['status'] in ['present', 'late', 'half_day']:
                    attendance.check_in_time = timezone.now().time()
                attendance.save()
                messages.success(request, f"Attendance marked for {form.cleaned_data['date']}!")
            
            return redirect('teacher_attendance:mark_attendance')
    else:
        form = TeacherAttendanceForm(teacher=teacher)
    
    # Get today's attendance
    today = timezone.now().date()
    today_attendance = TeacherAttendance.objects.filter(
        teacher=teacher,
        date=today
    ).first()
    
    # Get recent attendance records
    recent_attendance = TeacherAttendance.objects.filter(
        teacher=teacher
    ).order_by('-date')[:10]
    
    context = {
        'form': form,
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'today': today,
    }
    
    return render(request, 'teacher_attendance/mark_attendance.html', context)


@login_required
def attendance_history(request):
    """View teacher attendance history"""
    teacher = request.user.teacher
    
    # Get filter parameters
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    status = request.GET.get('status', '')
    
    # Build query
    queryset = TeacherAttendance.objects.filter(teacher=teacher)
    
    if month and year:
        queryset = queryset.filter(date__month=int(month), date__year=int(year))
    
    if status:
        queryset = queryset.filter(status=status)
    
    attendance_records = queryset.order_by('-date')
    
    # Calculate statistics
    total_days = queryset.count()
    present_days = queryset.filter(status__in=['present', 'late', 'half_day']).count()
    absent_days = queryset.filter(status='absent').count()
    leave_days = queryset.filter(status='on_leave').count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    context = {
        'attendance_records': attendance_records,
        'month': int(month),
        'year': int(year),
        'status_filter': status,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'attendance_percentage': attendance_percentage,
        'months': [(i, timezone.datetime(2024, i, 1).strftime('%B')) for i in range(1, 13)],
        'years': [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    }
    
    return render(request, 'teacher_attendance/attendance_history.html', context)


@login_required
def edit_attendance(request, pk):
    """Edit an existing attendance record"""
    teacher = request.user.teacher
    attendance = get_object_or_404(TeacherAttendance, pk=pk, teacher=teacher)
    
    if request.method == 'POST':
        form = TeacherAttendanceForm(request.POST, instance=attendance, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance record updated successfully!")
            return redirect('teacher_attendance:attendance_history')
    else:
        form = TeacherAttendanceForm(instance=attendance, teacher=teacher)
    
    context = {
        'form': form,
        'attendance': attendance,
        'edit_mode': True,
    }
    
    return render(request, 'teacher_attendance/mark_attendance.html', context)


@login_required
def delete_attendance(request, pk):
    """Delete an attendance record"""
    teacher = request.user.teacher
    attendance = get_object_or_404(TeacherAttendance, pk=pk, teacher=teacher)
    
    if request.method == 'POST':
        date = attendance.date
        attendance.delete()
        messages.success(request, f"Attendance record for {date} deleted successfully!")
        return redirect('teacher_attendance:attendance_history')
    
    context = {
        'attendance': attendance,
    }
    
    return render(request, 'teacher_attendance/delete_confirm.html', context)


@login_required
def dashboard_stats(request):
    """Get teacher attendance statistics for dashboard"""
    teacher = request.user.teacher
    today = timezone.now().date()
    
    # Today's attendance
    today_attendance = TeacherAttendance.objects.filter(
        teacher=teacher,
        date=today
    ).first()
    
    # This month's stats
    this_month = timezone.now().month
    this_year = timezone.now().year
    
    month_records = TeacherAttendance.objects.filter(
        teacher=teacher,
        date__month=this_month,
        date__year=this_year
    )
    
    month_present = month_records.filter(status__in=['present', 'late', 'half_day']).count()
    month_absent = month_records.filter(status='absent').count()
    month_leave = month_records.filter(status='on_leave').count()
    
    # Overall stats
    total_records = TeacherAttendance.objects.filter(teacher=teacher).count()
    total_present = TeacherAttendance.objects.filter(
        teacher=teacher,
        status__in=['present', 'late', 'half_day']
    ).count()
    
    overall_percentage = (total_present / total_records * 100) if total_records > 0 else 0
    
    context = {
        'today_attendance': today_attendance,
        'month_present': month_present,
        'month_absent': month_absent,
        'month_leave': month_leave,
        'overall_percentage': round(overall_percentage, 1),
        'total_records': total_records,
    }
    
    return context
