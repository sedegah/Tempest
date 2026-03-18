from celery import shared_task
from django.utils import timezone
from .models import SharedFile
from .interfaces import StorageInterface, DBInterface

@shared_task
def delete_expired_files():
    from django.db.models import F
    expired_files = SharedFile.objects.filter(download_count__gte=F('max_downloads')) | SharedFile.objects.filter(expires_at__lt=timezone.now())
    
    deleted_count = 0
    for file_record in expired_files:
        try:
            if file_record.file:
                StorageInterface.delete_file(file_record.file.name)
            DBInterface.delete_file_record(file_record)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting file record {file_record.token}: {e}")
            
    return f"Deleted {deleted_count} expired files."
