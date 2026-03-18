import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_r2_api():
    account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
    bucket_name = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME')
    token = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    
    filename = "test_api_upload.txt"
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{filename}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain"
    }
    
    print(f"Testing R2 API...")
    print(f"Endpoint: {endpoint}")
    
    # 1. PUT
    print("Attempting PUT...")
    res = requests.put(endpoint, data="Hello Cloudflare R2", headers=headers)
    print(f"PUT Status: {res.status_code}")
    if res.status_code not in [200, 201]:
        print(f"PUT Error: {res.text}")
        return

    # 2. HEAD
    print("Attempting HEAD...")
    res = requests.head(endpoint, headers=headers)
    print(f"HEAD Status: {res.status_code}")
    
    # 3. GET
    print("Attempting GET...")
    res = requests.get(endpoint, headers=headers)
    print(f"GET Status: {res.status_code}")
    if res.status_code == 200:
        print(f"GET Content: {res.text}")

if __name__ == "__main__":
    test_r2_api()
