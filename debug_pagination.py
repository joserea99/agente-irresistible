
import os
import requests
import json
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Check for API key
API_KEY = os.environ.get("BRANDFOLDER_API_KEY")
if not API_KEY:
    try:
        with open('.env') as f:
            for line in f:
                if 'BRANDFOLDER_API_KEY' in line:
                    API_KEY = line.split('=')[1].strip()
                    break
    except:
        pass

if not API_KEY:
    print("❌ Error: BRANDFOLDER_API_KEY not found.")
    exit(1)

BRANDFOLDER_API_BASE = "https://brandfolder.com/api/v4"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def check_structure():
    print("🔍 Checking API Response Structure...")
    
    # Get BF ID
    resp = requests.get(f"{BRANDFOLDER_API_BASE}/brandfolders", headers=HEADERS)
    bf_id = resp.json().get("data", [])[0]["id"]
    
    # Request Assets
    url = f"{BRANDFOLDER_API_BASE}/brandfolders/{bf_id}/assets"
    params = {"per": 100} 
    
    resp = requests.get(url, headers=HEADERS, params=params)
    result = resp.json()
    
    print(f"🔑 Response Keys: {list(result.keys())}")
    
    if "meta" in result:
        print(f"📄 Meta Keys: {list(result['meta'].keys())}")
        if "pagination" in result['meta']:
             print(f"📄 Pagination: {result['meta']['pagination']}")
        else:
             print("⚠️ 'pagination' key missing from 'meta'")
    else:
        print("❌ 'meta' key missing from response")
        
    # Try fetching page 2 just in case parameter based pagination works
    print("re-trying with page=2...")
    params['page'] = 2
    resp2 = requests.get(url, headers=HEADERS, params=params)
    assets2 = resp2.json().get("data", [])
    print(f"📦 Assets on Page 2: {len(assets2)}")
    
    if len(assets2) > 0:
        print("✅ Pagination Confirmed: Page 2 returned data.")
        print("💡 The application needs to loop through pages to get everything.")

if __name__ == "__main__":
    check_structure()
