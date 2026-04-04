"""
Workspace App Forms - Note and File Forms
"""
from django import forms
from .models import TeacherNote, TeacherFile


class TeacherNoteForm(forms.ModelForm):
    """
    Form for creating and updating teacher notes.
    """
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Note Title'
        })
    )
    content = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Write your note here...'
        })
    )
    is_pinned = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = TeacherNote
        fields = ['title', 'content', 'is_pinned']

    def clean_title(self):
        """Validate title"""
        title = self.cleaned_data.get('title')
        if title and not title.strip():
            raise forms.ValidationError('Title is required.')
        return title.strip() if title else title

    def clean_content(self):
        """Validate content"""
        content = self.cleaned_data.get('content')
        if content and not content.strip():
            raise forms.ValidationError('Content is required.')
        return content


class TeacherFileForm(forms.ModelForm):
    """
    Form for uploading teacher files.
    """
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'File Title'
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
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = TeacherFile
        fields = ['title', 'description', 'file']

    def clean_file(self):
        """Validate file type and size"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError('File size must be less than 10MB.')
            
            # Check file extension
            valid_extensions = [
                '.pdf', '.docx', '.doc', '.xlsx', '.xls',
                '.png', '.jpg', '.jpeg', '.gif', '.txt'
            ]
            ext = '.' + file.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(f'File type {ext} is not allowed. Allowed types: {", ".join(valid_extensions)}')
            
            # Try to validate MIME type using magic library
            try:
                import magic
                mime = magic.from_buffer(file.read(1024), mime=True)
                file.seek(0)  # Reset file pointer
                
                valid_mimes = [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'image/png',
                    'image/jpeg',
                    'image/gif',
                    'text/plain'
                ]
                
                if mime not in valid_mimes:
                    # Allow if we can't determine MIME type but extension is valid
                    pass
            except ImportError:
                # magic library not installed, skip MIME validation
                pass
        
        return file

    def clean_title(self):
        """Validate title"""
        title = self.cleaned_data.get('title')
        if title and not title.strip():
            raise forms.ValidationError('Title is required.')
        return title.strip() if title else title
