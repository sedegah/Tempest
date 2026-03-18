import os
import hashlib
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from cryptography.fernet import Fernet
from .models import SharedFile, AccessLog
from .forms import UploadForm
from .interfaces import StorageInterface, DBInterface
from django.contrib.auth.hashers import make_password, check_password
from django_ratelimit.decorators import ratelimit

def file_status_view(request, token, original_uuid):
    shared_file = get_object_or_404(SharedFile, token=original_uuid)
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
            shared_file = form.save(commit=False)
            
            raw_password = form.cleaned_data.get('password')
            if raw_password:
                shared_file.password = make_password(raw_password)

            encrypt = form.cleaned_data.get('encrypt', False)
            if encrypt:
                encrypted_data, file_key = encrypt_file(request.FILES['file'])
                
                from django.core.files.base import ContentFile
                shared_file.file.save(request.FILES['file'].name, ContentFile(encrypted_data), save=False)
                shared_file.encryption_key = file_key
            
            shared_file.save()
            
            secure_token = get_obfuscated_token(shared_file.token)
            return redirect('success', token=secure_token, original_uuid=shared_file.token)
    else:
        form = UploadForm()
    
    return render(request, 'upload.html', {'form': form})

def success_view(request, token, original_uuid):
    shared_file = get_object_or_404(SharedFile, token=original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
        
    link = request.build_absolute_uri(f'/download/{token}/{original_uuid}/')
    return render(request, 'success.html', {'link': link, 'file': shared_file})

@ratelimit(key='ip', rate='20/m', block=True)
def download_view(request, token, original_uuid):
    shared_file = get_object_or_404(SharedFile, token=original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
    
    
    log = AccessLog.objects.create(
        shared_file=shared_file,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    if shared_file.is_expired():
        log.success = False
        log.save()
        return render(request, 'link_expired.html', status=410)

    if shared_file.password:
        attempts = int(request.session.get(f'pwd_attempts_{original_uuid}', 0))
        if request.method == 'POST':
            pwd = request.POST.get('password', '')
            if not check_password(pwd, shared_file.password):
                attempts += 1
                request.session[f'pwd_attempts_{original_uuid}'] = attempts
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
                # Correct password
                request.session[f'auth_ok_{original_uuid}'] = True
                request.session.pop(f'pwd_attempts_{original_uuid}', None)
                # Success - will proceed to render download.html
        else:
            return render(request, 'download_auth.html', {
                'token': token, 'original_uuid': original_uuid,
                'shared_file': shared_file, 'panel': 'auth',
                'attempts': attempts, 'attempts_remaining': 3 - attempts,
            })

    # If already authenticated or no password, show landing page
    return render(request, 'download.html', {
        'token': token,
        'original_uuid': original_uuid,
        'shared_file': shared_file
    })

@ratelimit(key='ip', rate='10/m', block=True)
def perform_download(request, token, original_uuid):
    shared_file = get_object_or_404(SharedFile, token=original_uuid)
    
    expected_token = get_obfuscated_token(shared_file.token)
    if token != expected_token:
        raise Http404()
    
    # Check if download is still valid (e.g. not one-time used already)
    if shared_file.is_expired():
         return render(request, 'link_expired.html', status=410)

    # Check password if applicable (session check)
    if shared_file.password:
        # Check if they have the session flag set by download_view authentication
        # We need a way to track successful auth. Let's use a session key.
        if not request.session.get(f'auth_ok_{original_uuid}'):
             return redirect('download', token=token, original_uuid=original_uuid)

    try:
        file_name = shared_file.file.name
        file_content = StorageInterface.get_file_content(file_name)
        if not file_content:
            if settings.DEBUG:
                from django.core.files.storage import default_storage
                last_url = getattr(default_storage, 'last_failed_url', 'Unknown URL')
                raise Http404(f"File not found in storage: {file_name} at {last_url}")
            raise Http404("File not found in storage.")

        if shared_file.encryption_key:
            decrypted_data = decrypt_file_content(file_content, shared_file.encryption_key)
            response = HttpResponse(decrypted_data, content_type='application/octet-stream')
        else:
            response = HttpResponse(file_content, content_type='application/octet-stream')

        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_name)}"'
        
        # Increment download count (multi-download logic)
        DBInterface.increment_download_count(shared_file)
        
        # Log the final download success
        AccessLog.objects.create(
            shared_file=shared_file,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return response

    except Exception as e:
        if settings.DEBUG:
            raise Http404(f"File could not be read: {str(e)}")
        raise Http404("File could not be read.")
