"""
Accounts App Views - Authentication, Dashboard, and Profile Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.cache import cache
from .models import Teacher
from .forms import TeacherRegistrationForm, TeacherLoginForm, TeacherProfileForm
from .decorators import teacher_login_required, ajax_required
import json

# Rate limiting settings
LOGIN_RATE_LIMIT = 5  # attempts per window
LOGIN_RATE_WINDOW = 60  # seconds (1 minute)


def custom_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)


def login_view(request):
    """
    Teacher login view with rate limiting.
    Handles both GET (display form) and POST (authenticate) requests.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        # Rate limiting check
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        cache_key = f'login_attempts_{ip_address}'
        
        attempts = cache.get(cache_key, 0)
        if attempts >= LOGIN_RATE_LIMIT:
            messages.error(request, f'Too many login attempts. Please try again after {LOGIN_RATE_WINDOW} seconds.')
            return render(request, 'accounts/login.html')
        
        form = TeacherLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = request.POST.get('remember_me')

            # Set session expiry based on remember me
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(60 * 60 * 8)  # 8 hours

            # Reset login attempts on successful login
            cache.delete(cache_key)
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.teacher.full_name or user.username}!')
            return redirect('dashboard:dashboard')
        else:
            # Increment failed attempts
            cache.set(cache_key, attempts + 1, LOGIN_RATE_WINDOW)
            messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = TeacherLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """
    Teacher registration view.
    Allows new teachers to create an account.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to EduTrack Pro.')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@teacher_login_required
def logout_view(request):
    """
    Logout view.
    Clears session and redirects to login page.
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@teacher_login_required
def profile_view(request):
    """
    Teacher profile view.
    Allows teachers to update their profile information.
    Shows system-wide stats for super admins.
    """
    teacher = request.user.teacher

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherProfileForm(instance=teacher)

    # Get statistics based on user role
    if teacher.is_super_admin:
        # For super admin, show system-wide stats
        from apps.students.models import Student, Batch
        total_students = Student.objects.count()
        total_batches = Batch.objects.count()
    else:
        # For regular teachers, show their own stats
        total_students = teacher.students.count()
        total_batches = teacher.batches.count()

    context = {
        'form': form,
        'teacher': teacher,
        'total_students': total_students,
        'total_batches': total_batches,
    }

    return render(request, 'accounts/profile.html', context)


@teacher_login_required
def dashboard_view(request):
    """
    Main teacher dashboard.
    Displays stats, charts, alerts, and today's timetable.
    Super admins are redirected to admin panel.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        return redirect('super_admin:dashboard')
    
    today = timezone.now().date()

    # Get teacher's students
    students = teacher.students.select_related('batch').all()
    total_students = students.count()

    # Get today's attendance (optimized with distinct count)
    today_attendance = teacher.attendance_records.filter(date=today)
    students_present_today = today_attendance.filter(status='present').values('student').distinct().count()
    students_absent_today = today_attendance.filter(status__in=['absent', 'late']).values('student').distinct().count()

    # Get batches
    batches = teacher.batches.all()
    total_batches = batches.count()

    # Get today's timetable (optimized)
    day_name = today.strftime('%A')
    todays_slots = teacher.timetable_slots.filter(day_of_week=day_name).select_related('batch').order_by('start_time')

    # Get low attendance students
    low_attendance_students = []
    for student in students:
        percentage = student.attendance_percentage
        if percentage < 75:
            low_attendance_students.append({
                'student': student,
                'percentage': percentage
            })
    low_attendance_students.sort(key=lambda x: x['percentage'])

    # Get recent notifications (optimized)
    notifications = teacher.notifications.filter(is_read=False).order_by('-created_at')[:5]

    context = {
        'total_students': total_students,
        'students_present_today': students_present_today,
        'students_absent_today': students_absent_today,
        'total_batches': total_batches,
        'todays_slots': todays_slots,
        'low_attendance_students': low_attendance_students[:5],
        'notifications': notifications,
        'today': today,
    }

    return render(request, 'dashboard/index.html', context)


# API Views for Dashboard
@teacher_login_required
@ajax_required
def dashboard_stats_api(request):
    """
    API endpoint for dashboard statistics.
    Returns JSON data for charts and stats cards.
    """
    teacher = request.user.teacher
    today = timezone.now().date()
    
    # Stats cards
    total_students = teacher.students.count()
    today_attendance = teacher.attendance_records.filter(date=today)
    students_present_today = today_attendance.filter(status='present').values('student').distinct().count()
    students_absent_today = today_attendance.filter(status__in=['absent', 'late']).values('student').distinct().count()
    total_batches = teacher.batches.count()
    
    # Weekly attendance data (last 7 days)
    weekly_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_attendance = teacher.attendance_records.filter(date=date)
        present = day_attendance.filter(status='present').values('student').distinct().count()
        absent = day_attendance.filter(status__in=['absent', 'late']).values('student').distinct().count()
        weekly_data.append({
            'day': date.strftime('%a'),
            'date': date.isoformat(),
            'present': present,
            'absent': absent
        })
    
    # Today's present vs absent for doughnut chart
    today_present = students_present_today
    today_absent = students_absent_today
    
    # Monthly trend (last 30 days)
    monthly_trend = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        day_attendance = teacher.attendance_records.filter(date=date)
        total = day_attendance.count()
        if total > 0:
            present = day_attendance.filter(status='present').count()
            percentage = round((present / total) * 100, 1)
        else:
            percentage = None
        monthly_trend.append({
            'date': date.isoformat(),
            'percentage': percentage
        })
    
    data = {
        'stats': {
            'total_students': total_students,
            'students_present_today': students_present_today,
            'students_absent_today': students_absent_today,
            'total_batches': total_batches
        },
        'weekly_chart': weekly_data,
        'today_chart': {
            'present': today_present,
            'absent': today_absent
        },
        'monthly_trend': monthly_trend
    }
    
    return JsonResponse(data)
