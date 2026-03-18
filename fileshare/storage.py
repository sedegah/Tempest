import os
import requests
import urllib.parse
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.conf import settings

@deconstructible
class CloudflareR2Storage(Storage):
    def __init__(self, **kwargs):
        self.account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID') or os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.bucket_name = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME')
        self.token = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
        self.endpoint = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects"
    def _get_url(self, name):
        safe_name = urllib.parse.quote(name, safe='/')
        return f"{self.endpoint}/{safe_name}"

    def _save(self, name, content):
        url = self._get_url(name)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/octet-stream"
        }
        content.seek(0)
        print(f"R2 PUT: {url}")
        res = requests.put(url, data=content.read(), headers=headers)
        if res.status_code not in [200, 201]:
            print(f"R2 PUT Error: {res.status_code} {res.text}")
            raise Exception(f"R2 Upload failed: {res.status_code} {res.text}")
        return name

    def _open(self, name, mode='rb'):
        public_url = os.environ.get('CLOUDFLARE_R2_PUBLIC_URL')
        if public_url:
            url = f"{public_url.rstrip('/')}/{name}"
            res = requests.get(url)
            if res.status_code == 200:
                from django.core.files.base import ContentFile
                return ContentFile(res.content, name=name)
        
        url = self._get_url(name)
        headers = {"Authorization": f"Bearer {self.token}"}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise Exception(f"R2 Download failed: {res.status_code} {res.text} at {url}")
        from django.core.files.base import ContentFile
        return ContentFile(res.content, name=name)

    def exists(self, name):
        public_url = os.environ.get('CLOUDFLARE_R2_PUBLIC_URL')
        if public_url:
            url = f"{public_url.rstrip('/')}/{name}"
            res = requests.head(url)
            if res.status_code == 200:
                return True
        
        url = self._get_url(name)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Range": "bytes=0-0"
        }
        res = requests.get(url, headers=headers)
        if res.status_code not in [200, 206] and settings.DEBUG:
            self.last_failed_url = url
        return res.status_code in [200, 206]

    def url(self, name):
        public_url = os.environ.get('CLOUDFLARE_R2_PUBLIC_URL', '')
        if public_url:
            return f"{public_url.rstrip('/')}/{name}"
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/r2/buckets/{self.bucket_name}/objects/{name}"
        
    def delete(self, name):
        url = self._get_url(name)
        headers = {"Authorization": f"Bearer {self.token}"}
        requests.delete(url, headers=headers)
