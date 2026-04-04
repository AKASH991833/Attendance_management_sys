"""
Super Admin Forms
"""
from django import forms
from django.contrib.auth.models import User
from apps.accounts.models import Teacher
from .models import SystemLog


class TeacherCreateForm(forms.ModelForm):
    """Form for creating new teachers"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}),
        help_text='Required. 150 characters or fewer.'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': True}),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_super_admin = forms.BooleanField(
        required=False,
        label='Grant Super Admin privileges',
        help_text='If checked, this teacher will have super admin access'
    )

    class Meta:
        model = Teacher
        fields = ['full_name', 'department', 'phone', 'is_super_admin']

    def clean_username(self):
        """Validate username is unique"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username

    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        """Create User and Teacher profile"""
        # Create User first - signal will auto-create Teacher profile
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['full_name'].split()[0] if ' ' in self.cleaned_data['full_name'] else self.cleaned_data['full_name'],
            last_name=' '.join(self.cleaned_data['full_name'].split()[1:]) if ' ' in self.cleaned_data['full_name'] else '',
            is_staff=True,
            is_active=True
        )
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()  # Signal will create Teacher here
            
            # Now update the auto-created teacher profile with form data
            teacher = user.teacher
            teacher.full_name = self.cleaned_data['full_name']
            teacher.department = self.cleaned_data.get('department', '')
            teacher.phone = self.cleaned_data.get('phone', '')
            teacher.is_super_admin = self.cleaned_data.get('is_super_admin', False)
            teacher.save()
            
        return user


class TeacherEditForm(forms.ModelForm):
    """Form for editing teacher profile"""
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_super_admin = forms.BooleanField(
        required=False,
        label='Grant Super Admin privileges',
        help_text='If checked, this teacher will have super admin access'
    )
    is_active = forms.BooleanField(
        required=False,
        label='Account Active',
        help_text='If unchecked, teacher cannot login'
    )

    class Meta:
        model = Teacher
        fields = ['full_name', 'department', 'phone', 'is_super_admin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['is_active'].initial = self.instance.user.is_active

    def clean_email(self):
        """Validate email is unique (excluding current user)"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        """Update User and Teacher profile"""
        if self.instance and self.instance.user:
            self.instance.user.email = self.cleaned_data['email']
            first_name = self.cleaned_data['full_name'].split()[0] if ' ' in self.cleaned_data['full_name'] else self.cleaned_data['full_name']
            last_name = ' '.join(self.cleaned_data['full_name'].split()[1:]) if ' ' in self.cleaned_data['full_name'] else ''
            self.instance.user.first_name = first_name
            self.instance.user.last_name = last_name
            self.instance.user.is_staff = True
            self.instance.user.is_active = self.cleaned_data.get('is_active', True)
            if commit:
                self.instance.user.save()
        return super().save(commit)


class SystemLogFilterForm(forms.Form):
    """Form for filtering system logs"""
    action = forms.ChoiceField(
        required=False,
        choices=[('', 'All Actions')] + [(k, v) for k, v in SystemLog.ACTION_CHOICES],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
