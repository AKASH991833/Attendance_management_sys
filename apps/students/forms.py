"""
Students App Forms - Student and Batch Forms
"""
from django import forms
from .models import Student, Batch
import re


class BatchForm(forms.ModelForm):
    """
    Form for creating and updating batches.
    """
    name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Batch Name (e.g., Batch A, Sem 3-2024)'
        })
    )
    semester = forms.ChoiceField(
        choices=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
        ],
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

    class Meta:
        model = Batch
        fields = ['name', 'semester', 'subject']


class StudentForm(forms.ModelForm):
    """
    Form for creating and updating students.
    Roll number is auto-generated from name.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name (e.g., Akash Kumar)',
            'autocomplete': 'off'
        })
    )
    roll_number = forms.CharField(
        max_length=20,
        required=False,  # Not required - will be auto-generated
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Auto-generated (e.g., AK001)',
            'readonly': 'readonly'  # Read-only for new students
        })
    )
    semester = forms.ChoiceField(
        choices=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
        ],
        required=True,
        widget=forms.Select(attrs={
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
    contact_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number (WhatsApp)'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address (Optional)'
        })
    )

    class Meta:
        model = Student
        fields = ['full_name', 'semester', 'batch', 'contact_number', 'email']

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        # Store teacher securely for use in validation
        # NEVER use teacher from POST data
        if teacher:
            self._current_teacher = teacher
            self.fields['batch'].queryset = teacher.batches.all()
            # Set initial batch if only one exists
            if teacher.batches.count() == 1:
                self.fields['batch'].initial = teacher.batches.first()

    def clean_contact_number(self):
        """Validate contact number format"""
        contact_number = self.cleaned_data.get('contact_number')
        if contact_number:
            # Remove any non-digit characters
            cleaned = re.sub(r'\D', '', contact_number)
            if len(cleaned) < 10:
                raise forms.ValidationError('Please enter a valid 10-digit contact number.')
            return cleaned
        return contact_number

    def clean_full_name(self):
        """Validate full name"""
        full_name = self.cleaned_data.get('full_name')
        if full_name and not full_name.strip():
            raise forms.ValidationError('Full name is required.')
        return full_name.strip() if full_name else full_name
