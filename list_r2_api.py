import requests
import os
from dotenv import load_dotenv

load_dotenv()

def list_r2_objects():
    account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
    bucket_name = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME')
    token = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    
    # R2 List Objects API (S3-compatible is better for listing, but let's try Client API)
    # The Client API v4 for R2 listing is a bit different.
    # Usually it's GET /accounts/{account_id}/r2/buckets/{bucket_name}/objects
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Listing R2 Objects via Client API...")
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        if data.get('success'):
            objects = data.get('result', [])
            print(f"Found {len(objects)} objects:")
            for obj in objects:
                print(f" - {obj.get('key')} ({obj.get('size')} bytes)")
        else:
            print(f"API Error: {data.get('errors')}")
    else:
        print(f"HTTP Error: {res.text}")

if __name__ == "__main__":
    list_r2_objects()
