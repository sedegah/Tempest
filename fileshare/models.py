# pyre-ignore-all-errors
import uuid
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Optional

@dataclass
class SharedFile:
    """
    Represents an independently uploaded file object.
    Replaces Django ORM (`models.Model`) to support JSON HTTP bindings for Cloudflare D1.
    """
    # Primary Key
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 12-char Obfuscated Token (Unique lookup parameter)
    token: str = field(default_factory=lambda: secrets.token_urlsafe(8)[:12])
    
    # Storage Backend Filename (R2 Blob Key)
    file_name: str = ""
    
    # User's Local Uploaded Filename
    original_name: str = ""
    
    # Temporal Control
    uploaded_at: datetime = field(default_factory=timezone.now)
    expires_at: datetime = field(default_factory=timezone.now)
    
    # Download Quota Boundaries
    max_downloads: int = 1
    download_count: int = 0
    
    # Optional Security Tiers
    encryption_key: Optional[str] = field(default=None, repr=False)
    password: Optional[str] = field(default=None, repr=False)

    def __str__(self):
        return f"<SharedFile: {self.original_name} (Expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})>"

    @property
    def downloaded(self):
        """Helper property explicitly tracking the current download count."""
        return self.download_count

    @property
    def display_name(self):
        """Returns the user-facing filename for templates."""
        return self.original_name

    def get_expiration_reason(self):
        """
        Returns a human-readable reason if the file is expired, otherwise None.
        """
        now = timezone.now()
        if now >= self.expires_at:
            return f"File expired by time limit (Expired at: {self.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC, Current: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
        if self.download_count >= self.max_downloads:
            return f"Download limit reached ({self.download_count}/{self.max_downloads} downloads used)"
        return None

    def is_expired(self):
        """
        Calculates if the file's strict maximum limits (TTL or Quotas) have been breached.
        """
        return self.get_expiration_reason() is not None


@dataclass
class AccessLog:
    """
    Independent metrics logging user-agent access requests mapping to a given SharedFile.
    """
    shared_file_id: str
    accessed_at: datetime = field(default_factory=timezone.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    
    # D1 Autoincrement PK
    id: Optional[int] = None

    def __str__(self):
        return f"<AccessLog: {self.shared_file_id} - {self.status} (IP: {self.ip_address})>"
