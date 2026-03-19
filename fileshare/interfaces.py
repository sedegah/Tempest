# pyre-ignore-all-errors
import os
import uuid
import json
import boto3
import requests
from datetime import datetime, timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from botocore.exceptions import ClientError
from .models import SharedFile, AccessLog

class StorageInterface:
    @staticmethod
    def upload_file(file_name, file_content):
        return default_storage.save(file_name, ContentFile(file_content))

    @staticmethod
    def get_file_content(file_path):
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as f:
                return f.read()
        return None

    @staticmethod
    def delete_file(file_path):
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            return True
        return False

    @staticmethod
    def get_r2_client():
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
        if not getattr(settings, 'USE_S3', False):
            return None
        client = StorageInterface.get_r2_client()
        try:
            return client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_name},
                ExpiresIn=expiration
            )
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

class D1Client:
    @staticmethod
    def execute(sql: str, params: list = None):
        account_id = os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID")
        database_id = os.environ.get("CLOUDFLARE_D1_DATABASE_ID", "2dd53748-6960-411a-ac3d-96f575645d1c")
        
        # Patch UUID safely globally if the local .env is outdated
        if len(database_id) == 35 and database_id.endswith("d1c"):
            database_id = database_id[:-3] + "5d1c"

        api_token = "q80U1FFuq8M9ObfVCROLIOi2Dl20361eec2FjGuC"
        
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"sql": sql}
        if params:
            payload["params"] = params
            
        resp = requests.post(url, headers=headers, json=payload)
        if not resp.ok:
            raise Exception(f"D1 API HTTP {resp.status_code} Error: {resp.text}")
            
        data = resp.json()
        if not data.get("success"):
            raise Exception(f"D1 API Error: {json.dumps(data.get('errors'))}")
            
        return data["result"][0]

class DBInterface:
    @staticmethod
    def create_shared_file(shared_file: SharedFile):
        sql = """
            INSERT INTO shared_files 
            (id, token, file_name, original_name, uploaded_at, expires_at, max_downloads, download_count, encryption_key, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            shared_file.id,
            shared_file.token,
            shared_file.file_name,
            shared_file.original_name,
            shared_file.uploaded_at.isoformat() if isinstance(shared_file.uploaded_at, datetime) else shared_file.uploaded_at,
            shared_file.expires_at.isoformat() if isinstance(shared_file.expires_at, datetime) else shared_file.expires_at,
            shared_file.max_downloads,
            shared_file.download_count,
            shared_file.encryption_key,
            shared_file.password
        ]
        D1Client.execute(sql, params)
        return shared_file

    @staticmethod
    def get_file_by_uuid(uuid_token: str):
        sql = "SELECT * FROM shared_files WHERE id = ? OR token = ?"
        res = D1Client.execute(sql, [str(uuid_token), str(uuid_token)])
        results = res.get("results", [])
        
        if not results:
            return None
            
        row = results[0]
        return SharedFile(
            id=row["id"],
            token=row["token"],
            file_name=row["file_name"],
            original_name=row["original_name"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")),
            max_downloads=row["max_downloads"],
            download_count=row["download_count"],
            encryption_key=row["encryption_key"],
            password=row["password"]
        )

    @staticmethod
    def increment_download_count(shared_file: SharedFile):
        shared_file.download_count += 1
        D1Client.execute(
            "UPDATE shared_files SET download_count = ? WHERE id = ?",
            [shared_file.download_count, shared_file.id]
        )
        return shared_file

    @staticmethod
    def delete_file_record(shared_file: SharedFile):
        StorageInterface.delete_file(shared_file.file_name)
        D1Client.execute("DELETE FROM shared_files WHERE id = ?", [shared_file.id])
        return True

    @staticmethod
    def get_expired_files():
        now = datetime.now(timezone.utc).isoformat()
        sql = "SELECT * FROM shared_files WHERE expires_at < ?"
        res = D1Client.execute(sql, [now])
        files = []
        for row in res.get("results", []):
            files.append(SharedFile(
                id=row["id"],
                token=row["token"],
                file_name=row["file_name"],
                original_name=row["original_name"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"].replace("Z", "+00:00")),
                expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")),
                max_downloads=row["max_downloads"],
                download_count=row["download_count"],
                encryption_key=row["encryption_key"],
                password=row["password"]
            ))
        return files

    @staticmethod
    def log_access(shared_file: SharedFile, ip_address: str, user_agent: str, status: str):
        sql = """
            INSERT INTO access_logs (shared_file_id, accessed_at, ip_address, user_agent, status)
            VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        D1Client.execute(sql, [shared_file.id, timestamp, ip_address, user_agent, status])
        return True

    @staticmethod
    def get_access_logs(shared_file: SharedFile):
        sql = "SELECT * FROM access_logs WHERE shared_file_id = ? ORDER BY accessed_at DESC"
        res = D1Client.execute(sql, [shared_file.id])
        logs = []
        for row in res.get("results", []):
            logs.append(AccessLog(
                id=row["id"],
                shared_file_id=row["shared_file_id"],
                accessed_at=datetime.fromisoformat(row["accessed_at"].replace("Z", "+00:00")),
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                status=row["status"]
            ))
        return logs
