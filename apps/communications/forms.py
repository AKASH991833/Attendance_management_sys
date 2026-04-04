"""
Communications App Forms - Broadcast Message Forms
"""
from django import forms
from .models import BroadcastMessage


class BroadcastMessageForm(forms.ModelForm):
    """
    Form for creating broadcast messages.
    """
    batch = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    message_type = forms.ChoiceField(
        choices=BroadcastMessage.MESSAGE_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    message = forms.CharField(
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter your message here...',
            'maxlength': '1000'
        })
    )

    class Meta:
        model = BroadcastMessage
        fields = ['batch', 'message_type', 'message']

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['batch'].queryset = teacher.batches.all()
            # Add "All Batches" option
            self.fields['batch'].empty_label = 'All Batches'

    def clean_message(self):
        """Validate message content"""
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) == 0:
            raise forms.ValidationError('Message cannot be empty.')
        if message and len(message) > 1000:
            raise forms.ValidationError('Message must be less than 1000 characters.')
        return message.strip() if message else message
