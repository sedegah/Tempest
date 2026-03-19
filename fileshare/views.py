# pyre-ignore-all-errors
import os
import hashlib
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from cryptography.fernet import Fernet
from .models import SharedFile, AccessLog
from .forms import UploadForm
from .interfaces import StorageInterface, DBInterface
from werkzeug.security import generate_password_hash, check_password_hash
from django_ratelimit.decorators import ratelimit
from links.models import ShortLink
from links.interfaces import ShortLinkDBInterface

def get_shared_file_or_404(original_uuid):
    shared_file = DBInterface.get_file_by_uuid(original_uuid)
    if not shared_file:
        raise Http404("File not found")
    return shared_file

def file_status_view(request, token, original_uuid):
    shared_file = get_shared_file_or_404(original_uuid)
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    return JsonResponse({
        'downloaded': shared_file.downloaded,
        'is_expired': shared_file.is_expired(),
        'expires_at_iso': shared_file.expires_at.isoformat(),
    })

def landing_view(request):
    return render(request, 'landing.html')

def features_view(request):
    return render(request, 'features.html')

def how_it_works_view(request):
    return render(request, 'how_it_works.html')

def tech_stack_view(request):
    return render(request, 'tech_stack.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def terms_view(request):
    return render(request, 'terms.html')

def documentation_view(request):
    return render(request, 'documentation.html')

def api_reference_view(request):
    return render(request, 'api_reference.html')

def get_encryption_key(file_specific_key=None):
    if file_specific_key:
        return file_specific_key.encode('utf-8')
    return settings.FILES_ENCRYPTION_KEY.encode('utf-8')

def encrypt_file(file_obj):
    key = Fernet.generate_key()
    fern = Fernet(key)
    encrypted_data = fern.encrypt(file_obj.read())
    return encrypted_data, key.decode('utf-8')

def decrypt_file_content(encrypted_data, key):
    fern = Fernet(key.encode('utf-8'))
    return fern.decrypt(encrypted_data)

def get_obfuscated_token(uuid_token):
    return hashlib.sha256(f"{uuid_token}{settings.SECRET_KEY}".encode()).hexdigest()[:32]

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_id = str(uuid.uuid4())
            file_token = secrets.token_urlsafe(8)[:12]
            
            raw_password = form.cleaned_data.get('password')
            hashed_password = generate_password_hash(raw_password) if raw_password else None
            
            expires_in_hours = float(form.cleaned_data.get('expires_in_hours', 24))
            expires_at = timezone.now() + timedelta(hours=expires_in_hours)
            
            uploaded_file = request.FILES['file']
            file_name = f"{file_id}_{uploaded_file.name}"
            
            encryption_key = None
            encrypt = form.cleaned_data.get('encrypt', False)
            if encrypt:
                encrypted_data, encryption_key = encrypt_file(uploaded_file)
                StorageInterface.upload_file(file_name, encrypted_data)
            else:
                StorageInterface.upload_file(file_name, uploaded_file.read())

            shared_file = SharedFile(
                id=file_id,
                token=file_token,
                file_name=file_name,
                original_name=uploaded_file.name,
                uploaded_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                max_downloads=form.cleaned_data.get('max_downloads', 1),
                download_count=0,
                encryption_key=encryption_key,
                password=hashed_password
            )
            
            DBInterface.create_shared_file(shared_file)
            
            # Create a ShortLink for this file (inheriting file limits)
            short_link = ShortLink(
                shared_file_id=shared_file.id,
                max_downloads=shared_file.max_downloads,
                expires_at=shared_file.expires_at
            )
            ShortLinkDBInterface.create_short_link(short_link)
            
            secure_token = get_obfuscated_token(shared_file.token)
            return redirect('success', token=secure_token, original_uuid=shared_file.id)
    else:
        form = UploadForm()
    
    return render(request, 'upload.html', {'form': form})

def success_view(request, token, original_uuid):
    shared_file = get_shared_file_or_404(original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
        
    # Fetch associated short link
    sql = "SELECT code FROM short_links WHERE shared_file_id = ? ORDER BY created_at DESC LIMIT 1"
    from fileshare.interfaces import D1Client
    res = D1Client.execute(sql, [shared_file.id])
    results = res.get("results", [])
    
    if results:
        short_code = results[0]["code"]
        short_url = request.build_absolute_uri(f'/d/{short_code}/')
    else:
        short_url = request.build_absolute_uri(f'/download/{token}/{original_uuid}/')

    return render(request, 'success.html', {'link': short_url, 'file': shared_file})

@ratelimit(key='ip', rate='20/m', block=True)
def download_view(request, token, original_uuid):
    shared_file = get_shared_file_or_404(original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
    
    if shared_file.is_expired():
        DBInterface.log_access(shared_file, get_client_ip(request), request.META.get('HTTP_USER_AGENT', ''), "expired")
        return render(request, 'link_expired.html', status=410)

    # Initial page load - no password challenge yet unless required
    if shared_file.password:
        attempts = int(request.session.get(f'pwd_attempts_{original_uuid}', 0))
        if request.method == 'POST':
            pwd = request.POST.get('password', '')
            if not check_password_hash(shared_file.password, pwd):
                attempts += 1
                request.session[f'pwd_attempts_{original_uuid}'] = attempts
                
                DBInterface.log_access(shared_file, get_client_ip(request), request.META.get('HTTP_USER_AGENT', ''), "auth_failed")
                
                if attempts >= 3:
                    request.session.pop(f'pwd_attempts_{original_uuid}', None)
                    DBInterface.delete_file_record(shared_file)
                    return render(request, 'download_auth.html', {
                        'panel': 'locked', 'token': token, 'original_uuid': original_uuid,
                    })
                return render(request, 'download_auth.html', {
                    'error': 'Incorrect password.',
                    'attempts': attempts,
                    'attempts_remaining': 3 - attempts,
                    'token': token, 'original_uuid': original_uuid,
                    'shared_file': shared_file, 'panel': 'auth',
                })
            else:
                request.session[f'auth_ok_{original_uuid}'] = True
                request.session.pop(f'pwd_attempts_{original_uuid}', None)
        else:
            return render(request, 'download_auth.html', {
                'token': token, 'original_uuid': original_uuid,
                'shared_file': shared_file, 'panel': 'auth',
                'attempts': attempts, 'attempts_remaining': 3 - attempts,
            })

    return render(request, 'download.html', {
        'token': token,
        'original_uuid': original_uuid,
        'shared_file': shared_file
    })

@ratelimit(key='ip', rate='10/m', block=True)
def perform_download(request, token, original_uuid):
    shared_file = get_shared_file_or_404(original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
    
    if shared_file.is_expired():
         return render(request, 'link_expired.html', status=410)

    if shared_file.password:
        if not request.session.get(f'auth_ok_{original_uuid}'):
             return redirect('download', token=token, original_uuid=original_uuid)

    try:
        file_name = shared_file.file_name
        file_content = StorageInterface.get_file_content(file_name)
        if not file_content:
            raise Http404("File not found in storage.")

        if shared_file.encryption_key:
            decrypted_data = decrypt_file_content(file_content, shared_file.encryption_key)
            response = HttpResponse(decrypted_data, content_type='application/octet-stream')
        else:
            response = HttpResponse(file_content, content_type='application/octet-stream')

        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(shared_file.original_name)}"'
        
        DBInterface.increment_download_count(shared_file)
        
        DBInterface.log_access(shared_file, get_client_ip(request), request.META.get('HTTP_USER_AGENT', ''), "success")
        return response

    except Exception as e:
        if settings.DEBUG:
            raise Http404(f"File could not be read: {str(e)}")
        raise Http404("File could not be read.")
