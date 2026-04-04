"""
Communications App Views - WhatsApp Broadcast Management
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import datetime
import json
import re
import time
import html
from .models import BroadcastMessage
from .forms import BroadcastMessageForm
from apps.accounts.decorators import teacher_login_required, ajax_required
from apps.students.models import Student

# Rate limiting settings
WHATSAPP_RATE_LIMIT_DELAY = 0.5  # seconds between messages
WHATSAPP_MAX_BATCH_SIZE = 100  # max messages per broadcast
WHATSAPP_MAX_MESSAGE_LENGTH = 1000  # max characters per message


@teacher_login_required
def broadcast_view(request):
    """
    View for creating and sending broadcast messages.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')

    # Get recent broadcasts
    recent_broadcasts = BroadcastMessage.objects.filter(teacher=teacher).order_by('-sent_at')[:10]

    context = {
        'recent_broadcasts': recent_broadcasts,
    }
    return render(request, 'communications/broadcast.html', context)


@teacher_login_required
@ajax_required
def send_broadcast_api(request):
    """
    API endpoint to send WhatsApp broadcast messages.
    Supports Twilio and Meta Cloud API providers.
    Falls back to simulation mode if API keys are not configured.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    teacher = request.user.teacher
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    # Validate content-type
    if request.content_type != 'application/json':
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    batch_id = data.get('batch_id')
    message_type = data.get('message_type', 'announcement')
    message_template = data.get('message', '')

    # Validate message type
    valid_types = ['holiday', 'attendance_alert', 'announcement']
    if not isinstance(message_type, str) or message_type not in valid_types:
        message_type = 'announcement'

    # Validate message is a string and within length limit
    if not isinstance(message_template, str):
        return JsonResponse({'error': 'Invalid request data'}, status=400)
    
    if not message_template or len(message_template) > WHATSAPP_MAX_MESSAGE_LENGTH:
        return JsonResponse({'error': f'Message must be between 1 and {WHATSAPP_MAX_MESSAGE_LENGTH} characters'}, status=400)

    # Sanitize message template to prevent XSS
    message_template = html.escape(message_template)
    
    # Get students to send to
    if batch_id:
        try:
            from apps.students.models import Batch
            batch = Batch.objects.get(pk=batch_id, teacher=teacher)
            students = batch.students.filter(is_active=True, contact_number__isnull=False).exclude(contact_number='')
        except:
            return JsonResponse({'error': 'Invalid request data'}, status=400)
    else:
        students = Student.objects.filter(
            teacher=teacher,
            is_active=True,
            contact_number__isnull=False
        ).exclude(contact_number='')

    if not students.exists():
        return JsonResponse({'error': 'No students with contact numbers found', 'field': 'batch_id'}, status=400)

    # Limit batch size for safety
    total_students = students.count()
    if total_students > WHATSAPP_MAX_BATCH_SIZE:
        students = students[:WHATSAPP_MAX_BATCH_SIZE]
        messages.warning(request, f'Message limited to first {WHATSAPP_MAX_BATCH_SIZE} students due to rate limiting')
    
    # Prepare message sending
    sent_count = 0
    failed_count = 0
    simulated = False
    
    # Get WhatsApp configuration
    whatsapp_provider = settings.WHATSAPP_PROVIDER
    twilio_sid = settings.TWILIO_ACCOUNT_SID
    twilio_token = settings.TWILIO_AUTH_TOKEN
    twilio_from = settings.TWILIO_WHATSAPP_FROM
    meta_token = settings.META_WHATSAPP_TOKEN
    meta_phone_id = settings.META_PHONE_NUMBER_ID
    
    # Check if we should simulate
    if whatsapp_provider == 'twilio' and (not twilio_sid or not twilio_token):
        simulated = True
    elif whatsapp_provider == 'meta' and (not meta_token or not meta_phone_id):
        simulated = True
    
    # Process each student
    for student in students:
        # Personalize message
        personalized_message = message_template
        personalized_message = personalized_message.replace('[Student Name]', student.full_name)
        personalized_message = personalized_message.replace('[Teacher Name]', teacher.full_name or teacher.user.username)
        
        # Replace other placeholders
        if '[Date]' in personalized_message:
            personalized_message = personalized_message.replace('[Date]', datetime.now().strftime('%Y-%m-%d'))
        if '[Holiday Title]' in personalized_message:
            personalized_message = personalized_message.replace('[Holiday Title]', 'Upcoming Holiday')
        if '[X]' in personalized_message:
            # Calculate attendance percentage
            total = student.attendance_records.count()
            if total > 0:
                present = student.attendance_records.filter(status='present').count()
                percentage = round((present / total) * 100, 1)
            else:
                percentage = 100
            personalized_message = personalized_message.replace('[X]', str(percentage))
        
        # Format phone number for WhatsApp
        phone = student.contact_number
        # Remove non-digit characters
        phone = re.sub(r'\D', '', phone)
        # Add country code if not present (default to India +91)
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        if simulated:
            # Simulation mode - log to console
            print(f"[SIMULATED] WhatsApp to +{phone}: {personalized_message}")
            sent_count += 1
        else:
            # Actual sending with rate limiting
            try:
                if whatsapp_provider == 'twilio':
                    sent = send_via_twilio(phone, personalized_message, twilio_sid, twilio_token, twilio_from)
                elif whatsapp_provider == 'meta':
                    sent = send_via_meta(phone, personalized_message, meta_phone_id, meta_token)
                else:
                    sent = False

                if sent:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting delay
                time.sleep(WHATSAPP_RATE_LIMIT_DELAY)
            except Exception as e:
                print(f"Error sending to {phone}: {str(e)}")
                failed_count += 1
    
    # Determine status
    if failed_count == 0:
        status = 'sent'
    elif sent_count == 0:
        status = 'failed'
    else:
        status = 'partial'
    
    # Save broadcast record
    broadcast = BroadcastMessage.objects.create(
        teacher=teacher,
        batch_id=batch_id if batch_id else None,
        message_type=message_type,
        message=message_template[:1000],
        sent_count=sent_count,
        failed_count=failed_count,
        status=status
    )
    
    return JsonResponse({
        'success': True,
        'sent': sent_count,
        'failed': failed_count,
        'simulated': simulated,
        'broadcast_id': broadcast.id,
        'message': f'Message sent to {sent_count} student(s)' + (f' ({failed_count} failed)' if failed_count > 0 else '')
    })


def send_via_twilio(phone, message, sid, token, from_number):
    """
    Send WhatsApp message via Twilio API.
    """
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(
            from_=from_number,
            to=f'whatsapp:+{phone}',
            body=message
        )
        return True
    except Exception as e:
        print(f"Twilio error: {str(e)}")
        return False


def send_via_meta(phone, message, phone_number_id, token):
    """
    Send WhatsApp message via Meta Cloud API.
    """
    try:
        import requests
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': message}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Meta API error: {str(e)}")
        return False


@teacher_login_required
@ajax_required
def get_broadcast_templates_api(request):
    """
    API endpoint to get message templates.
    """
    teacher = request.user.teacher
    teacher_name = teacher.full_name or teacher.user.username
    
    templates = {
        'holiday': f"Dear [Student Name], [Holiday Title] holiday on [Date]. College is closed. – {teacher_name}",
        'attendance_alert': f"Dear [Student Name], your attendance is [X]%. Please attend regularly. – {teacher_name}",
        'announcement': f"Dear [Student Name], – {teacher_name}"
    }
    
    return JsonResponse({'templates': templates})
