from django import forms
from django.core.exceptions import ValidationError
from .models import SharedFile
from datetime import timedelta
from django.utils import timezone
import os

EXPIRY_CHOICES = [
    (1, '1 Hour'),
    (24, '1 Day'),
    (168, '1 Week'),
    (720, '1 Month'),
]

MAX_FILE_SIZE = 100 * 1024 * 1024
DOWNLOAD_CHOICES = [
    (1, '1 Download'),
    (5, '5 Downloads'),
    (10, '10 Downloads'),
    (100, '100 Downloads'),
]

class UploadForm(forms.Form):
    file = forms.FileField()
    password = forms.CharField(max_length=128, required=False)
    encrypt = forms.BooleanField(required=False, initial=True)
    expires_in_hours = forms.ChoiceField(
        choices=[
            (0.166, '10 Minutes'),
            (1, '1 Hour'),
            (5, '5 Hours'),
            (24, '24 Hours'),
            (72, '3 Days'),
            (168, '1 Week')
        ],
        initial=24
    )
    max_downloads = forms.IntegerField(min_value=1, max_value=100, initial=1)
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > MAX_FILE_SIZE:
                raise ValidationError("File size must be under 50MB.")
            
            ext = os.path.splitext(file.name)[1].lower()
            if ext in ['.exe', '.bat', '.sh', '.bin', '.cmd', '.msi']:
                raise ValidationError("Executable files are not allowed.")
        return file

    def save(self, commit=True):
        instance = super().save(commit=False)
        hours = int(self.cleaned_data.get('expires_in_hours', 24))
        instance.expires_at = timezone.now() + timedelta(hours=hours)
        if commit:
            instance.save()
        return instance
