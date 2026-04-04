"""
Teacher Attendance Forms
"""
from django import forms
from django.utils import timezone
from .models import TeacherAttendance


class TeacherAttendanceForm(forms.ModelForm):
    """Form for marking teacher attendance"""
    
    class Meta:
        model = TeacherAttendance
        fields = ['date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes (e.g., reason for absence)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        # Set initial date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().strftime('%Y-%m-%d')
        
        # Update status choices with icons
        self.fields['status'].choices = [
            ('present', '✓ Present'),
            ('absent', '✗ Absent'),
            ('late', '⏰ Late'),
            ('on_leave', '🏖 On Leave'),
            ('half_day', '⏱ Half Day'),
        ]

    def clean_date(self):
        """Validate that date is not in the future"""
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("You cannot mark attendance for future dates.")
        return date

    def save(self, commit=True):
        """Save the attendance record with teacher"""
        instance = super().save(commit=False)
        if self.teacher:
            instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance


class TeacherAttendanceBulkForm(forms.Form):
    """Form for bulk marking of teacher attendance"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True
        })
    )
    status = forms.ChoiceField(
        choices=[
            ('present', '✓ Present'),
            ('absent', '✗ Absent'),
            ('late', '⏰ Late'),
            ('on_leave', '🏖 On Leave'),
            ('half_day', '⏱ Half Day'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional notes'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().strftime('%Y-%m-%d')
