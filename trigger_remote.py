import requests
import sys
import time
import os

# Configuration
BACKEND_URL = "https://web-production-7054f.up.railway.app"
MIGRATION_SECRET = "irresistible-migration-force-2026"

def print_header():
    print("\n" + "="*50)
    print("   IRRESISTIBLE AGENT - TERMINAL CONTROL")
    print("="*50)

def trigger_migration():
    print(f"\n🚀 Triggering Legacy Data Migration...")
    url = f"{BACKEND_URL}/auth/migrate-force"
    headers = {"X-Migration-Secret": MIGRATION_SECRET}
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Migration Request Sent!")
            print(f"👉 Server Response: {response.json()}")
            print("Note: This runs in the background. Check Railway logs for progress.")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")

def trigger_rebuild_kb():
    print(f"\n📚 Triggering Knowledge Base Rebuild (Sync)...")
    # Using the /ingest endpoint. It usually requires parameters.
    # We will trigger a default ingest of the first Brandfolder.
    url = f"{BACKEND_URL}/brandfolder/ingest"
    
    # Payload for default ingest (first 50 assets to start)
    payload = {
        "max_assets": 50
    }
    
    try:
        print(f"📡 Sending request to {url}...")
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Ingestion Started!")
            print(f"👉 Server Response: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")

def check_health():
    url = f"{BACKEND_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"🟢 Server is ONLINE ({BACKEND_URL})")
            return True
        else:
            print(f"🔴 Server returned status {response.status_code}")
            return False
    except:
        print(f"🔴 Cannot connect to {BACKEND_URL}")
        return False

def main():
    print_header()
    
    if not check_health():
        print("⚠️  Cannot proceed if server is down or unreachable.")
        sys.exit(1)

    print("\nSelect an action:")
    print("1. [MIGRATE] Recover Legacy Data (ChromaDB -> Supabase)")
    print("2. [REBUILD] Re-Ingest Knowledge Base from Brandfolder")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        trigger_migration()
    elif choice == "2":
        trigger_rebuild_kb()
    elif choice == "3":
        print("Bye!")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
