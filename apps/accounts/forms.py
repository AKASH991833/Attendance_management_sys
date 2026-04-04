"""
Accounts App Forms - Authentication and Profile Forms
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Teacher
import re


class TeacherRegistrationForm(UserCreationForm):
    """
    Form for teacher self-registration.
    Includes all required fields for creating a teacher account.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department (Optional)'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'department', 'phone', 'password1', 'password2']

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_password1(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Password must contain at least one number.')
        return password

    def clean_full_name(self):
        """Clean and validate full name"""
        full_name = self.cleaned_data.get('full_name')
        if not full_name.strip():
            raise forms.ValidationError('Full name is required.')
        return full_name.strip()

    def save(self, commit=True):
        """Save user and create teacher profile"""
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name'].split()[0] if self.cleaned_data['full_name'] else ''
        user.last_name = ' '.join(self.cleaned_data['full_name'].split()[1:]) if len(self.cleaned_data['full_name'].split()) > 1 else ''
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Update teacher profile
            teacher = user.teacher
            teacher.full_name = self.cleaned_data['full_name']
            teacher.department = self.cleaned_data.get('department', '')
            teacher.phone = self.cleaned_data.get('phone', '')
            teacher.save()
        return user


class TeacherLoginForm(AuthenticationForm):
    """
    Custom login form with styled widgets.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_username(self):
        """Normalize email/username"""
        username = self.cleaned_data.get('username')
        return username.strip().lower()


class TeacherProfileForm(forms.ModelForm):
    """
    Form for updating teacher profile.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Teacher
        fields = ['full_name', 'department', 'phone', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def clean_profile_picture(self):
        """Validate profile picture with secure content checking"""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (max 2MB)
            if profile_picture.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Profile picture must be less than 2MB.')
            
            # Check file extension
            ext = profile_picture.name.split('.')[-1].lower()
            valid_extensions = ['jpg', 'jpeg', 'png']
            if ext not in valid_extensions:
                raise forms.ValidationError('Only JPG and PNG files are allowed.')
            
            # Validate actual image content using PIL
            from PIL import Image, UnidentifiedImageError
            try:
                # Open and verify image
                img = Image.open(profile_picture)
                img.verify()  # Verify it's a valid image
                
                # Reopen after verify (verify() makes image unusable)
                profile_picture.seek(0)
                img = Image.open(profile_picture)
                
                # Check image format
                if img.format not in ['JPEG', 'PNG']:
                    raise forms.ValidationError('Only JPG and PNG files are allowed.')
                    
            except UnidentifiedImageError:
                raise forms.ValidationError('Invalid image file. Please upload a valid image.')
            except Exception as e:
                raise forms.ValidationError(f'Error processing image: {str(e)}')
                
        return profile_picture

    def clean_full_name(self):
        """Validate full name"""
        full_name = self.cleaned_data.get('full_name')
        if not full_name.strip():
            raise forms.ValidationError('Full name is required.')
        return full_name.strip()

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def save(self, commit=True):
        """Save teacher profile and update user"""
        teacher = super().save(commit=commit)
        teacher.user.email = self.cleaned_data['email']
        teacher.user.first_name = self.cleaned_data['full_name'].split()[0] if self.cleaned_data['full_name'] else ''
        teacher.user.last_name = ' '.join(self.cleaned_data['full_name'].split()[1:]) if len(self.cleaned_data['full_name'].split()) > 1 else ''
        if commit:
            teacher.user.save()
        return teacher
