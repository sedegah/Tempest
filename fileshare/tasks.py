# pyre-ignore-all-errors
from celery import shared_task
from .models import SharedFile
from .interfaces import DBInterface, StorageInterface
import os
import zipfile
import shutil
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_file_path(file_path):
    key = Fernet.generate_key()
    fern = Fernet(key)
    with open(file_path, 'rb') as f:
        data = f.read()
    encrypted_data = fern.encrypt(data)
    with open(file_path, 'wb') as f:
        f.write(encrypted_data)
    return key.decode('utf-8')

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

@shared_task
def process_upload_task(shared_file_id, temp_file_paths, encrypt, is_multiple, original_name, final_file_name, temp_dir):
    """
    Handles Zipping, Encryption, and Upload to R2 in the background.
    """
    try:
        final_file_path = temp_file_paths[0]
        
        # 1. Zip if multiple files
        if is_multiple:
            zip_path = os.path.join(temp_dir, original_name)
            # Use ZIP_STORED to prevent massive CPU overhead and timeout crashes
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zip_file:
                for tfp in temp_file_paths:
                    zip_file.write(tfp, arcname=os.path.basename(tfp))
            final_file_path = zip_path

        # 2. Encrypt if required
        encryption_key = None
        if encrypt:
            encryption_key = encrypt_file_path(final_file_path)

        # 3. Upload to Storage (R2)
        with open(final_file_path, 'rb') as f:
            StorageInterface.upload_file(final_file_name, f.read())

        # 4. Update Database
        # We need to set download_count to 0 (was -1) and save encryption key
        sql = "UPDATE shared_files SET download_count = 0, encryption_key = ? WHERE id = ?"
        from .interfaces import D1Client
        D1Client.execute(sql, [encryption_key, shared_file_id])
        
    except Exception as e:
        print(f"Upload task failed for {shared_file_id}: {str(e)}")
        # If it fails, could optionally set download_count = -2 for error state
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
