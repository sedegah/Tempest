# pyre-ignore-all-errors
from celery import shared_task
from .models import SharedFile
from .interfaces import DBInterface

@shared_task
def delete_expired_files():
    """
    Periodically checks for expired files in D1 and deletes them natively from both R2 and D1.
    """
    expired_files = DBInterface.get_expired_files()
    
    deleted_count = 0
    for shared_file in expired_files:
        try:
            DBInterface.delete_file_record(shared_file)
            deleted_count += 1
        except Exception as e:
            print(f"Error sweeping {shared_file.id}: {e}")
            
    return f"Deleted {deleted_count} expired files from D1 & R2."
