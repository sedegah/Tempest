# pyre-ignore-all-errors
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from .interfaces import ShortLinkDBInterface
from fileshare.interfaces import DBInterface

def short_redirect_view(request, code):
    """
    Handles redirection from /d/<code> to the actual secure download page.
    Performs security and validation checks.
    """
    # 1. Fetch the short link record
    link = ShortLinkDBInterface.get_link_by_code(code)
    if not link:
        return HttpResponseNotFound("Link not found.")
        
    # 2. Check if link is active/expired
    if link.is_expired():
        return render(request, "link_expired.html", status=403)
        
    # 3. Fetch the associated SharedFile for deeper validation
    shared_file = DBInterface.get_file_by_uuid(link.shared_file_id)
    if not shared_file:
        return HttpResponseNotFound("Associated file no longer exists.")
        
    if shared_file.is_expired():
        return render(request, "link_expired.html", status=403)
        
    # 4. Increment download count for the link
    ShortLinkDBInterface.increment_usage(link)
    
    # 5. Redirect to the fileshare download page
    # Note: We use the SharedFile's token/id for the redirect
    return redirect('download', file_id=shared_file.token)
