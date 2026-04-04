"""
Reports App Views - Report Generation and Export
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, FloatField
from django.db.models.functions import Cast
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import json
from apps.accounts.decorators import teacher_login_required, ajax_required
from apps.students.models import Student, Batch
from apps.attendance.models import AttendanceRecord


@teacher_login_required
def reports_view(request):
    """
    Main reports page with report type selection.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.shortcuts import redirect
        return redirect('super_admin:dashboard')
    
    batches = teacher.batches.all()

    context = {
        'batches': batches,
    }
    return render(request, 'reports/generate.html', context)


@teacher_login_required
@ajax_required
def report_data_api(request):
    """
    API endpoint to get report data based on parameters.
    """
    teacher = request.user.teacher
    
    # Redirect super admins to admin panel
    if teacher.is_super_admin:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Access denied. Please use admin panel.'}, status=403)

    report_type = request.GET.get('type', 'batch')
    batch_id = request.GET.get('batch_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    specific_date = request.GET.get('specific_date')
    
    if report_type == 'batch':
        return get_batch_attendance_report(teacher, batch_id, from_date, to_date)
    elif report_type == 'low_attendance':
        return get_low_attendance_report(teacher)
    elif report_type == 'daily':
        return get_daily_summary_report(teacher, specific_date)
    else:
        return JsonResponse({'error': 'Invalid report type'}, status=400)


def get_batch_attendance_report(teacher, batch_id, from_date, to_date):
    """
    Get attendance report for a batch and date range.
    """
    if not batch_id or not from_date or not to_date:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    try:
        batch = Batch.objects.get(pk=batch_id, teacher=teacher)
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    except (Batch.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    students = batch.students.filter(is_active=True).order_by('roll_number')

    report_data = []
    for student in students:
        attendance = student.get_attendance_for_date_range(from_date, to_date)
        report_data.append({
            'id': student.id,
            'roll_number': student.roll_number,
            'full_name': student.full_name,
            'total_classes': attendance['total'],
            'present': attendance['present'],
            'absent': attendance['absent'],
            'percentage': attendance['percentage']
        })

    return JsonResponse({
        'report_type': 'batch',
        'batch': {'id': batch.id, 'name': batch.name, 'semester': batch.semester},
        'from_date': from_date.isoformat(),
        'to_date': to_date.isoformat(),
        'students': report_data
    })


def get_low_attendance_report(teacher):
    """
    Get report of students with low attendance (< 75%).
    Optimized with single query using annotations.
    """
    from django.db.models import Count, Q
    
    students = teacher.students.filter(is_active=True).annotate(
        total_classes=Count('attendance_records'),
        present_count=Count('attendance_records', filter=Q(attendance_records__status='present'))
    ).order_by('batch__name', 'roll_number')

    low_attendance_students = []
    for student in students:
        if student.total_classes > 0:
            percentage = round((student.present_count / student.total_classes) * 100, 1)
            if percentage < 75:
                low_attendance_students.append({
                    'id': student.id,
                    'roll_number': student.roll_number,
                    'full_name': student.full_name,
                    'batch': student.batch.name,
                    'total_classes': student.total_classes,
                    'present': student.present_count,
                    'absent': student.total_classes - student.present_count,
                    'percentage': percentage
                })

    return JsonResponse({
        'report_type': 'low_attendance',
        'threshold': 75,
        'students': low_attendance_students
    })


def get_daily_summary_report(teacher, specific_date):
    """
    Get daily attendance summary for a specific date.
    """
    if not specific_date:
        return JsonResponse({'error': 'Missing date parameter'}, status=400)
    
    try:
        date = datetime.strptime(specific_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    batches = teacher.batches.all()
    summary = []
    
    for batch in batches:
        records = AttendanceRecord.objects.filter(
            teacher=teacher,
            batch=batch,
            date=date
        )
        present = records.filter(status='present').count()
        absent = records.filter(status__in=['absent', 'late']).count()
        total = records.count()
        
        if total > 0:
            summary.append({
                'batch_id': batch.id,
                'batch_name': batch.name,
                'subject': batch.subject,
                'total': total,
                'present': present,
                'absent': absent,
                'percentage': round((present / total) * 100, 1) if total > 0 else 0
            })
    
    return JsonResponse({
        'report_type': 'daily',
        'date': date.isoformat(),
        'batches': summary
    })


@teacher_login_required
def export_excel(request):
    """
    Export report data to Excel file.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    report_type = data.get('type')
    report_data = data.get('data', {})
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Report'
    
    # Styles
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4f46e5', end_color='4f46e5', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    if report_type == 'batch':
        # Headers
        headers = ['Roll Number', 'Name', 'Total Classes', 'Present', 'Absent', 'Percentage']
        ws.append(headers)
        
        # Style header row
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Data rows
        students = report_data.get('students', [])
        for student in students:
            percentage_color = '00ff00' if student['percentage'] >= 75 else ('ffa500' if student['percentage'] >= 60 else 'ff0000')
            ws.append([
                student['roll_number'],
                student['full_name'],
                student['total_classes'],
                student['present'],
                student['absent'],
                f"{student['percentage']}%"
            ])
        
        # Set column widths
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
    
    elif report_type == 'low_attendance':
        headers = ['Roll Number', 'Name', 'Batch', 'Total Classes', 'Present', 'Absent', 'Percentage']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        students = report_data.get('students', [])
        for student in students:
            ws.append([
                student['roll_number'],
                student['full_name'],
                student['batch'],
                student['total_classes'],
                student['present'],
                student['absent'],
                f"{student['percentage']}%"
            ])
    
    elif report_type == 'daily':
        headers = ['Batch', 'Subject', 'Total', 'Present', 'Absent', 'Percentage']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        batches = report_data.get('batches', [])
        for batch in batches:
            ws.append([
                batch['batch_name'],
                batch.get('subject', ''),
                batch['total'],
                batch['present'],
                batch['absent'],
                f"{batch['percentage']}%"
            ])
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Create response
    filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@teacher_login_required
def export_pdf(request):
    """
    Export report data to PDF file.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    report_type = data.get('type')
    report_data = data.get('data', {})
    teacher = request.user.teacher
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    # Header
    title = Paragraph(f"EduTrack Pro - Attendance Report", title_style)
    elements.append(title)
    
    teacher_name = Paragraph(f"Teacher: {teacher.full_name or teacher.user.username}", styles['Normal'])
    elements.append(teacher_name)
    
    # Report type specific content
    if report_type == 'batch':
        batch_info = report_data.get('batch', {})
        from_date = report_data.get('from_date', '')
        to_date = report_data.get('to_date', '')
        
        subtitle = Paragraph(f"Batch: {batch_info.get('name', '')} | Period: {from_date} to {to_date}", styles['Normal'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [['Roll No', 'Name', 'Total', 'Present', 'Absent', 'Percentage']]
        for student in report_data.get('students', []):
            table_data.append([
                student['roll_number'],
                student['full_name'],
                str(student['total_classes']),
                str(student['present']),
                str(student['absent']),
                f"{student['percentage']}%"
            ])
    
    elif report_type == 'low_attendance':
        subtitle = Paragraph("Students with Attendance Below 75%", styles['Normal'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        table_data = [['Roll No', 'Name', 'Batch', 'Total', 'Present', 'Absent', 'Percentage']]
        for student in report_data.get('students', []):
            table_data.append([
                student['roll_number'],
                student['full_name'],
                student['batch'],
                str(student['total_classes']),
                str(student['present']),
                str(student['absent']),
                f"{student['percentage']}%"
            ])
    
    elif report_type == 'daily':
        date = report_data.get('date', '')
        subtitle = Paragraph(f"Daily Summary for {date}", styles['Normal'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        table_data = [['Batch', 'Subject', 'Total', 'Present', 'Absent', 'Percentage']]
        for batch in report_data.get('batches', []):
            table_data.append([
                batch['batch_name'],
                batch.get('subject', ''),
                str(batch['total']),
                str(batch['present']),
                str(batch['absent']),
                f"{batch['percentage']}%"
            ])
    else:
        table_data = [['No data available']]
    
    # Create table
    table = Table(table_data, colWidths=[1*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
    
    # Table style
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Create response
    buffer.seek(0)
    filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
