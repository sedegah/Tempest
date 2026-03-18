import uuid
from django.db import models
from django.utils import timezone

class SharedFile(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    max_downloads = models.PositiveIntegerField(default=1)
    download_count = models.PositiveIntegerField(default=0)
    encryption_key = models.CharField(max_length=128, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)

    def is_expired(self):
        return timezone.now() > self.expires_at or self.download_count >= self.max_downloads

    @property
    def display_name(self):
        import os
        return self.original_name or os.path.basename(self.file.name)

    def __str__(self):
        return f"File {self.token} (Expires: {self.expires_at})"

class AccessLog(models.Model):
    shared_file = models.ForeignKey(SharedFile, on_delete=models.CASCADE, related_name='access_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} Access to {self.shared_file.token} at {self.timestamp}"
