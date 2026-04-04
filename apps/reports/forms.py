"""
Reports App Forms - Report Generation Forms
"""
from django import forms
from django.utils import timezone
from apps.students.models import Batch


class AttendanceReportForm(forms.Form):
    """
    Form for generating attendance reports.
    """
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Batch'
    )
    from_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='From Date'
    )
    to_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='To Date'
    )
    export_format = forms.ChoiceField(
        choices=[
            ('html', 'View Online'),
            ('excel', 'Excel (.xlsx)'),
            ('pdf', 'PDF'),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        initial='html',
        label='Export Format'
    )
    
    def __init__(self, teacher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        
        if teacher:
            self.fields['batch'].queryset = Batch.objects.filter(teacher=teacher)
        
        # Set default date range (last 30 days)
        from datetime import timedelta
        if not self.data.get('from_date'):
            self.fields['from_date'].initial = timezone.now().date() - timedelta(days=30)
        if not self.data.get('to_date'):
            self.fields['to_date'].initial = timezone.now().date()
        
        self.fields['batch'].label_suffix = ''
        self.fields['from_date'].label_suffix = ''
        self.fields['to_date'].label_suffix = ''


class DailySummaryReportForm(forms.Form):
    """
    Form for generating daily attendance summary.
    """
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Date'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date to today
        if not self.data.get('date'):
            self.fields['date'].initial = timezone.now().date()
        
        self.fields['date'].label_suffix = ''


class LowAttendanceReportForm(forms.Form):
    """
    Form for low attendance report (no inputs required).
    """
    threshold = forms.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        initial=75,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
        }),
        label='Attendance Threshold (%)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['threshold'].label_suffix = ''
