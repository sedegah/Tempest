# pyre-ignore-all-errors
import uuid
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.utils import timezone
from .interfaces import ShortLinkDBInterface
from fileshare.interfaces import DBInterface
from fileshare.views import get_obfuscated_token

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
    now = timezone.now()
    if link.expires_at and now >= link.expires_at:
        return render(request, 'link_expired.html', {"reason": "Link expired by time limit"}, status=403)
        
    if link.download_count >= link.max_downloads:
        return render(request, 'link_expired.html', {"reason": f"Download limit reached ({link.download_count}/{link.max_downloads})"}, status=403)

    # Validation logic (File level inheritance)
    if shared_file.is_expired():
        return render(request, 'link_expired.html', status=403)

    # Increment usage count for the link
    ShortLinkDBInterface.increment_usage(link)
    
    # Log access for the file
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    DBInterface.log_access(shared_file, ip_address, user_agent, status="success")
    
    # Redirect to the download page (which handles its own auth)
    secure_token = get_obfuscated_token(shared_file.token)
    return redirect('download', token=secure_token, original_uuid=shared_file.id)
