import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load .env
load_dotenv()

from fileshare.interfaces import D1Client

def run_migration():
    sql = """
    CREATE TABLE IF NOT EXISTS short_links (
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        shared_file_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        max_downloads INTEGER DEFAULT 1,
        download_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (shared_file_id) REFERENCES shared_files (id)
    );
    """
    try:
        print("Running D1 migration for short_links table...")
        # Check if environment variables are loaded
        account_id = os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID")
        if not account_id:
            print("ERROR: CLOUDFLARE_R2_ACCOUNT_ID not found in environment.")
            return

        res = D1Client.execute(sql)
        print("Migration results:", res)
        # Verify result structure
        if res.get("success") == False:
            print("Migration Error:", res.get("errors"))
        else:
            print("Migration successful (or table already exists).")
    except Exception as e:
        print(f"Migration failed Exception: {e}")

if __name__ == "__main__":
    run_migration()
