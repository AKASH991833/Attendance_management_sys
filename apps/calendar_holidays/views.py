"""
Calendar & Holidays App Views - Calendar and Holiday Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from .models import Holiday
from .forms import HolidayForm
from apps.accounts.decorators import teacher_login_required, ajax_required
import json


# Static India-based holidays (fallback when no API)
INDIA_HOLIDAYS = {
    # Fixed date holidays
    '01-26': {'title': 'Republic Day', 'type': 'holiday', 'icon': '🇮🇳'},
    '08-15': {'title': 'Independence Day', 'type': 'holiday', 'icon': '🇮🇳'},
    '10-02': {'title': 'Gandhi Jayanti', 'type': 'holiday', 'icon': '🕊️'},
    '01-01': {'title': 'New Year', 'type': 'holiday', 'icon': '🎉'},
    '12-25': {'title': 'Christmas', 'type': 'holiday', 'icon': '🎄'},
}


def get_static_holidays(year):
    """
    Get static India holidays for a given year.
    Returns dict with date objects as keys.
    """
    holidays = {}
    for date_str, holiday_data in INDIA_HOLIDAYS.items():
        try:
            month, day = map(int, date_str.split('-'))
            holiday_date = datetime(year, month, day).date()
            holidays[holiday_date] = holiday_data
        except (ValueError, TypeError):
            continue
    return holidays


@teacher_login_required
def calendar_view(request):
    """
    Display calendar view with holidays and events.
    Shows red dots on Sundays and holidays.
    """
    teacher = request.user.teacher

    # Get current month and year from request or use today's date
    today = timezone.now().date()
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = today.month
        year = today.year

    # Validate month and year
    if month < 1 or month > 12:
        month = today.month
    if year < 2000 or year > 2100:
        year = today.year

    # Get calendar data
    first_day, num_days = monthrange(year, month)

    # Get holidays for this month from database
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)

    db_holidays = Holiday.objects.filter(
        teacher=teacher,
        date__range=[month_start, month_end]
    )

    # Get static India holidays for this year
    static_holidays = get_static_holidays(year)

    # Create a unified dict of holidays by date (DB takes priority)
    holidays_by_date = {}
    
    # First add static holidays
    for date, holiday_data in static_holidays.items():
        if date.month == month and date.year == year:
            holidays_by_date[date.day] = holiday_data
    
    # Then add DB holidays (overwrites static if same date)
    for holiday in db_holidays:
        holidays_by_date[holiday.date.day] = {
            'title': holiday.title,
            'type': holiday.type,
            'icon': holiday.icon,
            'description': holiday.description
        }

    # Get days with attendance marked
    attendance_dates = set()
    attendance_records = teacher.attendance_records.filter(
        date__range=[month_start, month_end]
    ).values_list('date', flat=True).distinct()
    for date in attendance_records:
        attendance_dates.add(date.day)

    # Build calendar grid with weekday info
    calendar_days = []
    current_day = 1

    # Empty cells for days before the first day of the month
    for i in range(first_day):
        calendar_days.append(None)

    # Days of the month with weekday info (Python: Monday=0, Sunday=6)
    while current_day <= num_days:
        # Calculate weekday for this day
        weekday = datetime(year, month, current_day).weekday()
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        calendar_days.append({
            'day': current_day,
            'weekday': weekday,
            'weekday_name': weekday_names[weekday],
            'is_sunday': weekday == 6,  # Sunday
            'is_saturday': weekday == 5,  # Saturday
            'is_today': current_day == today.day and month == today.month and year == today.year
        })
        current_day += 1
    
    context = {
        'month': month,
        'year': year,
        'month_name': datetime(year, month, 1).strftime('%B %Y'),
        'calendar_days': calendar_days,
        'holidays_by_date': holidays_by_date,
        'attendance_dates': attendance_dates,
        'today': today,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
    }
    return render(request, 'calendar_holidays/calendar.html', context)


@teacher_login_required
@ajax_required
def holiday_add_api(request):
    """
    API endpoint to add a holiday.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    teacher = request.user.teacher
    
    # Verify teacher account is active
    if not teacher.user.is_active:
        return JsonResponse({'error': 'Account disabled'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    date_str = data.get('date')
    title = data.get('title')
    holiday_type = data.get('type', 'holiday')
    description = data.get('description', '')
    
    # Validate required fields
    if not date_str or not title:
        return JsonResponse({'error': 'Missing required fields', 'field': 'date/title'}, status=400)
    
    # Parse date
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format', 'field': 'date'}, status=400)
    
    # Check if holiday already exists for this date
    existing = Holiday.objects.filter(teacher=teacher, date=date).first()
    if existing:
        return JsonResponse({'error': 'Holiday already exists for this date', 'field': 'date'}, status=400)
    
    # Validate type
    valid_types = ['holiday', 'exam', 'event']
    if holiday_type not in valid_types:
        holiday_type = 'holiday'
    
    # Create holiday
    holiday = Holiday.objects.create(
        teacher=teacher,
        date=date,
        title=title[:150],
        type=holiday_type,
        description=description[:1000] if description else ''
    )
    
    return JsonResponse({
        'success': True,
        'holiday': {
            'id': holiday.id,
            'date': holiday.date.isoformat(),
            'title': holiday.title,
            'type': holiday.type,
            'icon': holiday.icon
        }
    })


@teacher_login_required
@ajax_required
def holiday_delete_api(request, holiday_id):
    """
    API endpoint to delete a holiday.
    """
    teacher = request.user.teacher
    holiday = get_object_or_404(Holiday, pk=holiday_id, teacher=teacher)
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    holiday.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Holiday deleted successfully'
    })


@teacher_login_required
@ajax_required
def holidays_list_api(request):
    """
    API endpoint to get holidays for a specific month/year.
    """
    teacher = request.user.teacher
    
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if not month or not year:
        return JsonResponse({'error': 'Missing month/year parameters'}, status=400)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid month/year'}, status=400)
    
    # Get holidays for the month
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    holidays = Holiday.objects.filter(
        teacher=teacher,
        date__range=[month_start, month_end]
    )
    
    holidays_data = [
        {
            'id': h.id,
            'date': h.date.isoformat(),
            'day': h.date.day,
            'title': h.title,
            'type': h.type,
            'icon': h.icon
        }
        for h in holidays
    ]
    
    return JsonResponse({'holidays': holidays_data})
