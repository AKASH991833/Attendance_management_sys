"""
Calendar & Holidays App Forms - Holiday Forms
"""
from django import forms
from .models import Holiday


class HolidayForm(forms.ModelForm):
    """
    Form for creating and updating holidays.
    """
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    title = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Holiday/Event Title'
        })
    )
    type = forms.ChoiceField(
        choices=Holiday.TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description (Optional)'
        })
    )

    class Meta:
        model = Holiday
        fields = ['date', 'title', 'type', 'description']
