"""
Notifications App Forms - Notification Management Forms
"""
from django import forms
from .models import Notification


class NotificationFilterForm(forms.Form):
    """
    Form for filtering notifications.
    """
    type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Notification.TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Type'
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('unread', 'Unread'),
            ('read', 'Read'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Status'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].label_suffix = ''
        self.fields['status'].label_suffix = ''
