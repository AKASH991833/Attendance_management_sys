"""
Notifications App Views - Notification Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Notification
from apps.accounts.decorators import teacher_login_required, ajax_required


@teacher_login_required
def notifications_view(request):
    """
    List all notifications for the logged-in teacher.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')

    # Get all notifications, unread first
    notifications = Notification.objects.filter(teacher=teacher)
    
    # Pagination
    paginator = Paginator(notifications, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unread count
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/list.html', context)


@teacher_login_required
@ajax_required
def mark_notification_read_api(request, notification_id):
    """
    API endpoint to mark a notification as read.
    """
    teacher = request.user.teacher
    
    if request.method not in ['POST', 'PUT']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    notification = get_object_or_404(Notification, pk=notification_id, teacher=teacher)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Notification marked as read'
    })


@teacher_login_required
@ajax_required
def mark_all_read_api(request):
    """
    API endpoint to mark all notifications as read.
    """
    teacher = request.user.teacher
    
    if request.method not in ['POST', 'PUT']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    Notification.objects.filter(teacher=teacher, is_read=False).update(is_read=True)
    
    return JsonResponse({
        'success': True,
        'message': 'All notifications marked as read'
    })


@teacher_login_required
@ajax_required
def unread_count_api(request):
    """
    API endpoint to get unread notification count.
    """
    teacher = request.user.teacher
    count = Notification.objects.filter(teacher=teacher, is_read=False).count()
    
    return JsonResponse({
        'unread_count': count
    })


@teacher_login_required
@ajax_required
def delete_notification_api(request, notification_id):
    """
    API endpoint to delete a notification.
    """
    teacher = request.user.teacher
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    notification = get_object_or_404(Notification, pk=notification_id, teacher=teacher)
    notification.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Notification deleted'
    })


@teacher_login_required
def create_holiday_reminder(request):
    """
    Utility view to create holiday reminders for upcoming holidays.
    Can be called periodically or on teacher login.
    """
    teacher = request.user.teacher
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Check for holidays tomorrow
    from apps.calendar_holidays.models import Holiday
    holidays_tomorrow = Holiday.objects.filter(
        teacher=teacher,
        date=tomorrow
    )
    
    for holiday in holidays_tomorrow:
        # Check if reminder already exists
        existing = Notification.objects.filter(
            teacher=teacher,
            type='holiday',
            message__icontains=holiday.title,
            created_at__date=today
        ).first()
        
        if not existing:
            Notification.objects.create(
                teacher=teacher,
                title=f'Reminder: {holiday.title}',
                message=f'Tomorrow ({tomorrow.strftime("%B %d, %Y")}) is {holiday.title}. {holiday.get_type_display()}.',
                type='holiday'
            )
    
    return redirect('dashboard')
