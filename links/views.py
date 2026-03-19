# pyre-ignore-all-errors
import uuid
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from datetime import datetime, timezone
from .interfaces import ShortLinkDBInterface
from fileshare.interfaces import DBInterface

def short_redirect_view(request, code):
    """
    Resolves a short code to a real file download page.
    Validates existence, expiry, and download limits.
    """
    link = ShortLinkDBInterface.get_link_by_code(code)
    
    if not link:
        return HttpResponseNotFound("Short link not found.")
        
    if not link.is_active:
        return HttpResponseForbidden("This link has been deactivated.")
        
    # Fetch the actual file metadata
    shared_file = DBInterface.get_file_by_uuid(link.shared_file_id)
    if not shared_file:
        return HttpResponseNotFound("The file associated with this link no longer exists.")
        
    # Validation logic (Link level)
    now = datetime.now(timezone.utc)
    if link.expires_at and now >= link.expires_at:
        return render(request, 'link_expired.html', status=403)
        
    if link.download_count >= link.max_downloads:
        return render(request, 'link_expired.html', {"reason": "Download limit reached"}, status=403)

    # Validation logic (File level inheritance)
    if shared_file.is_expired():
        return render(request, 'link_expired.html', status=403)

    # Increment usage count for the link
    ShortLinkDBInterface.increment_usage(link)
    
    # Log access for the file
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    DBInterface.log_access(shared_file, ip_address, user_agent, status="success")
    
    # Build the redirection URL
    # Redirect to the download authentication page or download page
    # If the file has a password, we redirect to download_auth
    if shared_file.password:
        return redirect('download_auth', token=shared_file.token)
    else:
        return redirect('download', token=shared_file.token)
