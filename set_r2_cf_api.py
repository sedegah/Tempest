import requests
import os
from dotenv import load_dotenv

load_dotenv()

account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
bucket_name = 'tempest-fileshare'
# Using the global API token from your context
api_token = "q80U1FFuq8M9ObfVCROLIOi2Dl20361eec2FjGuC"

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/lifecycle"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# The Cloudflare R2 native lifecycle JSON structure
payload = {
    "rules": [
        {
            "id": "DeleteOldFiles72h",
            "conditions": {
                "prefix": ""
            },
            "action": {
                "type": "Delete"
            },
            "age": 259200
        }
    ]
}

resp = requests.put(url, headers=headers, json=payload)
print("STATUS:", resp.status_code)
print("RESPONSE:", resp.text)
