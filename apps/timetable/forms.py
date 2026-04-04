"""
Timetable App Forms - Timetable Slot Forms
"""
from django import forms
from .models import TimetableSlot
from django.core.exceptions import ValidationError


class TimetableSlotForm(forms.ModelForm):
    """
    Form for creating and updating timetable slots.
    """
    day_of_week = forms.ChoiceField(
        choices=TimetableSlot.DAY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    start_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    end_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'type': 'time',
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
    subject = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject Name'
        })
    )
    room = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Room Number (Optional)'
        })
    )

    class Meta:
        model = TimetableSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'batch', 'subject', 'room']

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['batch'].queryset = teacher.batches.all()

    def clean(self):
        """Validate time range and check for conflicts"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day_of_week = cleaned_data.get('day_of_week')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('End time must be after start time.')
        
        # Check for time conflicts (only if we have all required data)
        if start_time and end_time and day_of_week:
            teacher = None
            if self.instance and self.instance.pk:
                teacher = self.instance.teacher
            elif self.data and 'teacher' in self.data:
                from apps.accounts.models import Teacher
                try:
                    teacher = Teacher.objects.get(pk=self.data.get('teacher'))
                except:
                    pass
            
            if teacher:
                # Get existing slots for this teacher on this day
                conflicts = TimetableSlot.objects.filter(
                    teacher=teacher,
                    day_of_week=day_of_week
                )
                if self.instance and self.instance.pk:
                    conflicts = conflicts.exclude(pk=self.instance.pk)
                
                for slot in conflicts:
                    # Check for overlap: start1 < end2 AND end1 > start2
                    if start_time < slot.end_time and end_time > slot.start_time:
                        raise ValidationError(
                            f"Time conflict with existing slot: {slot.batch.name} "
                            f"on {day_of_week} from {slot.start_time} to {slot.end_time}"
                        )
        
        return cleaned_data
