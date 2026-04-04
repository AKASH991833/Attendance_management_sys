"""
Attendance App Forms - Attendance Forms
"""
from django import forms
from .models import AttendanceRecord
from apps.students.models import Batch


class AttendanceMarkForm(forms.Form):
    """
    Form for selecting batch and date for marking attendance.
    """
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    batch = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    timetable_slot = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['batch'].queryset = teacher.batches.all()
    
    def set_timetable_slots(self, batch_id, date):
        """Filter timetable slots by batch and day of week"""
        from datetime import datetime
        if batch_id:
            day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A') if isinstance(date, str) else date.strftime('%A')
            self.fields['timetable_slot'].queryset = self.fields['batch'].queryset.filter(
                id=batch_id,
                timetable_slots__day_of_week=day_name
            ).first().timetable_slots.filter(day_of_week=day_name) if self.fields['batch'].queryset.filter(id=batch_id).exists() else type(self.fields['timetable_slot'].queryset.model).objects.none()


class AttendanceHistoryFilterForm(forms.Form):
    """
    Form for filtering attendance history.
    """
    batch = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    student_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student name'
        })
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['batch'].queryset = teacher.batches.all()
