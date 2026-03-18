import boto3
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from botocore.exceptions import ClientError
from .models import SharedFile

class StorageInterface:
    """Interface to handle file operations across local storage and Cloudflare R2."""

    @staticmethod
    def upload_file(file_name, file_content):
        """Uploads a file using the configured storage backend (Local or R2)."""
        return default_storage.save(file_name, ContentFile(file_content))

    @staticmethod
    def get_file_content(file_path):
        """Retrieves raw file content."""
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as f:
                return f.read()
        return None

    @staticmethod
    def delete_file(file_path):
        """Deletes a file from the backend."""
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            return True
        return False

    @staticmethod
    def get_r2_client():
        """Returns a configured boto3 client for direct Cloudflare R2 interaction if needed."""
        if not getattr(settings, 'USE_S3', False):
            raise ValueError("S3/R2 is not configured. USE_S3 is False.")

        return boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='auto'
        )

    @staticmethod
    def generate_presigned_url(file_name, expiration=3600):
        """Generates a pre-signed URL for direct download from Cloudflare R2."""
        if not getattr(settings, 'USE_S3', False):
            return None

        client = StorageInterface.get_r2_client()
        try:
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': file_name
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None


class DBInterface:
    """Interface to handle explicit database operations related to our files."""

    @staticmethod
    def get_file_by_uuid(uuid_token):
        try:
            return SharedFile.objects.get(token=uuid_token)
        except SharedFile.DoesNotExist:
            return None

    @staticmethod
    def mark_as_downloaded(shared_file):
        shared_file.downloaded = True
        shared_file.save(update_fields=['downloaded'])
        return shared_file

    @staticmethod
    def delete_file_record(shared_file):
        StorageInterface.delete_file(shared_file.file.name)
        shared_file.delete()
        return True
