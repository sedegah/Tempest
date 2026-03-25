import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def execute(sql: str, params: list = None):
    account_id = os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID")
    database_id = os.environ.get("CLOUDFLARE_D1_DATABASE_ID", "2dd53748-6960-411a-ac3d-96f575645d1c")
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
        print(f"HTTP Error: {resp.status_code} {resp.text}")
        return None
        
    data = resp.json()
    return data

res = execute("SELECT * FROM shared_files ORDER BY uploaded_at DESC LIMIT 1")
print(f"System Now (UTC): {datetime.now(timezone.utc).isoformat()}")

if res and res.get("success"):
    row = res["result"][0]["results"]
    if row:
        print("Last Row in shared_files:")
        print(json.dumps(row[0], indent=2))
        
        uploaded_at_str = row[0]["uploaded_at"]
        expires_at_str = row[0]["expires_at"]
        
        print(f"Uploaded at: {uploaded_at_str}")
        print(f"Expires at: {expires_at_str}")
        
        try:
            # Replicating logic in interfaces.py
            parsed_uploaded = datetime.fromisoformat(uploaded_at_str.replace("Z", "+00:00"))
            parsed_expires = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            print(f"Parsed Uploaded: {parsed_uploaded}")
            print(f"Parsed Expires: {parsed_expires}")
            print(f"Comparison (Now >= Expires): {datetime.now(timezone.utc) >= parsed_expires}")
        except Exception as e:
            print(f"Parsing error: {e}")
    else:
        print("No rows found.")
else:
    print("Failed to fetch data.")
