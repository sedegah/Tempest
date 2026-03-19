# pyre-ignore-all-errors
import uuid
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

@dataclass
class ShortLink:
    """
    Represents a clean alias for a secure download resource.
    Maps a public 'code' (e.g., abc123) to a SharedFile via its ID.
    """
    # Unique slug for public URL (e.g., /d/abc123)
    code: str = field(default_factory=lambda: ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8)))
    
    # ID of the SharedFile this link points to
    shared_file_id: str = ""
    
    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    # Utilization Thresholds
    max_downloads: int = 1
    download_count: int = 0
    
    # Operational Status
    is_active: bool = True
    
    # Primary Key (D1)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self):
        return f"<ShortLink: {self.code} -> {self.shared_file_id}>"

    def is_expired(self):
        """
        Calculates if the short link itself (independent of the file) has expired.
        """
        now = datetime.now(timezone.utc)
        if self.expires_at and now >= self.expires_at:
            return True
        if self.download_count >= self.max_downloads:
            return True
        return not self.is_active
