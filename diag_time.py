import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def execute(sql: str, params: list = None):
    acc = os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID")
    db = os.environ.get("CLOUDFLARE_D1_DATABASE_ID", "2dd53748-6960-411a-ac3d-96f575645d1c")
    tok = "q80U1FFuq8M9ObfVCROLIOi2Dl20361eec2FjGuC"
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/d1/database/{db}/query"
    r = requests.post(url, headers={"Authorization": f"Bearer {tok}"}, json={"sql": sql, "params": params or []})
    return r.json()

data = execute("SELECT * FROM shared_files ORDER BY uploaded_at DESC LIMIT 1")
if data.get("success") and data["result"][0]["results"]:
    res = data["result"][0]["results"][0]
    up_str = res["uploaded_at"]
    ex_str = res["expires_at"]
    print(f"RAW UP: {up_str}")
    print(f"RAW EX: {ex_str}")
    
    parsed_up = datetime.fromisoformat(up_str.replace("Z", "+00:00"))
    parsed_ex = datetime.fromisoformat(ex_str.replace("Z", "+00:00"))
    
    print(f"PARSED UP: {parsed_up.isoformat()} (Aware: {parsed_up.tzinfo is not None})")
    print(f"PARSED EX: {parsed_ex.isoformat()} (Aware: {parsed_ex.tzinfo is not None})")
    
    now = datetime.now(timezone.utc)
    print(f"NOW: {now.isoformat()}")
    
    try:
        expired = now >= parsed_ex
        print(f"IS EXPIRED: {expired}")
    except TypeError as e:
        print(f"COMPARISON ERROR: {e}")
else:
    print("No data found or request failed.")
