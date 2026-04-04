"""
Timetable App Views - Timetable Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import TimetableSlot
from .forms import TimetableSlotForm
from apps.accounts.decorators import teacher_login_required, ajax_required
import json


@teacher_login_required
def timetable_list_view(request):
    """
    Display timetable as a weekly grid.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')

    # Get all slots for this teacher
    slots = teacher.timetable_slots.select_related('batch').all()

    # Organize by day
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_by_day = {}

    for day in days:
        day_slots = slots.filter(day_of_week=day).order_by('start_time')
        timetable_by_day[day] = day_slots

    # Calculate stats
    total_slots = slots.count()
    total_minutes = sum(slot.duration_minutes for slot in slots)
    total_hours = round(total_minutes / 60, 1) if total_minutes > 0 else 0
    total_batches = slots.values('batch').distinct().count()
    total_rooms = slots.exclude(room='').values('room').distinct().count()

    context = {
        'days': days,
        'timetable_by_day': timetable_by_day,
        'total_slots': total_slots,
        'total_hours': total_hours,
        'total_batches': total_batches,
        'total_rooms': total_rooms,
    }
    return render(request, 'timetable/list.html', context)


@teacher_login_required
def timetable_manage_view(request):
    """
    Manage timetable slots - add, edit, delete.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')
    
    slots = teacher.timetable_slots.select_related('batch').order_by('day_of_week', 'start_time')

    # Calculate stats
    unique_subjects = slots.values('subject').distinct().count()
    unique_batches = slots.values('batch').distinct().count()

    context = {
        'slots': slots,
        'unique_subjects': unique_subjects,
        'unique_batches': unique_batches,
    }
    return render(request, 'timetable/manage.html', context)


@teacher_login_required
def slot_add_view(request):
    """
    Add a new timetable slot.
    """
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = TimetableSlotForm(request.POST, teacher=teacher)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.teacher = teacher
            slot.save()
            messages.success(request, f'Timetable slot added for {slot.batch.name} on {slot.day_of_week}.')
            return redirect('timetable:timetable-manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimetableSlotForm(teacher=teacher)
    
    return render(request, 'timetable/slot_form.html', {'form': form, 'action': 'add'})


@teacher_login_required
def slot_edit_view(request, slot_id):
    """
    Edit an existing timetable slot.
    """
    teacher = request.user.teacher
    slot = get_object_or_404(TimetableSlot, pk=slot_id, teacher=teacher)
    
    if request.method == 'POST':
        form = TimetableSlotForm(request.POST, instance=slot, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Timetable slot updated for {slot.batch.name} on {slot.day_of_week}.')
            return redirect('timetable:timetable-manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TimetableSlotForm(instance=slot, teacher=teacher)
    
    return render(request, 'timetable/slot_form.html', {'form': form, 'slot': slot, 'action': 'edit'})


@teacher_login_required
def slot_delete_view(request, slot_id):
    """
    Delete a timetable slot.
    """
    teacher = request.user.teacher
    slot = get_object_or_404(TimetableSlot, pk=slot_id, teacher=teacher)
    
    if request.method == 'POST':
        slot_info = f"{slot.batch.name} on {slot.day_of_week}"
        slot.delete()
        messages.success(request, f'Timetable slot deleted: {slot_info}.')
        return redirect('timetable:timetable-manage')
    
    return render(request, 'timetable/slot_delete.html', {'slot': slot})


@teacher_login_required
@ajax_required
def slot_check_conflict_api(request):
    """
    API endpoint to check for time slot conflicts.
    """
    teacher = request.user.teacher
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    day = data.get('day_of_week')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    exclude_id = data.get('exclude_id')
    
    if not all([day, start_time, end_time]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    # Parse times
    from datetime import datetime
    try:
        start = datetime.strptime(start_time, '%H:%M').time()
        end = datetime.strptime(end_time, '%H:%M').time()
    except ValueError:
        return JsonResponse({'error': 'Invalid time format'}, status=400)
    
    # Check for conflicts
    conflicts = TimetableSlot.objects.filter(
        teacher=teacher,
        day_of_week=day
    )
    
    if exclude_id:
        conflicts = conflicts.exclude(pk=exclude_id)
    
    for slot in conflicts:
        # Check for overlap: start1 < end2 AND end1 > start2
        if start < slot.end_time and end > slot.start_time:
            return JsonResponse({
                'has_conflict': True,
                'conflicting_slot': {
                    'id': slot.id,
                    'batch': slot.batch.name,
                    'day': slot.day_of_week,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'subject': slot.subject
                }
            })
    
    return JsonResponse({'has_conflict': False})
