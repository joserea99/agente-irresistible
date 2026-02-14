
import os
import requests
import tempfile
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# --- COPY OF BrandfolderAPI CLASS (to avoid import hell) ---
BRANDFOLDER_API_BASE = "https://brandfolder.com/api/v4"

class BrandfolderAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BRANDFOLDER_API_KEY")
        if not self.api_key:
            raise ValueError("Brandfolder API key not provided!")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{BRANDFOLDER_API_BASE}{endpoint}"
        try:
            response = requests.request(method=method, url=url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error: {e}")
            return {"error": str(e), "data": []}
            
    def get_brandfolders(self) -> List[Dict]:
        result = self._request("GET", "/brandfolders")
        return result.get("data", [])

    def _map_attachments_to_assets(self, assets: List[Dict], included: List[Dict]) -> List[Dict]:
        # Minimal implementation for testing
        return assets
        
    # --- THE CRITICAL METHOD TO TEST ---
    def get_assets(self, section_id: str = None, collection_id: str = None, 
                   brandfolder_id: str = None, include_attachments: bool = True,
                   per_page: int = 100) -> List[Dict]:
        
        params = {"per": per_page}
        if include_attachments:
            params["include"] = "attachments"
        
        if section_id:
            endpoint = f"/sections/{section_id}/assets"
        elif collection_id:
            endpoint = f"/collections/{collection_id}/assets"
        elif brandfolder_id:
            endpoint = f"/brandfolders/{brandfolder_id}/assets"
        else:
            raise ValueError("Must provide ID")
        
        # Initial request
        print(f"📡 Requesting page 1 (per_page={per_page})...")
        result = self._request("GET", endpoint, params)
        
        assets = result.get("data") or []
        included = result.get("included") or []
        
        # Pagination Loop
        meta = result.get("meta", {})
        # Updated logic: check next_page directly
        next_page = meta.get("next_page")
        
        page_count = 1
        
        while next_page:
            print(f"📄 Found next page: {next_page}...")
            
            params["page"] = next_page
            print(f"📡 Requesting page {params['page']}...")
            result = self._request("GET", endpoint, params)
            
            new_assets = result.get("data") or []
            
            if not new_assets:
                print("⚠️ Page returned no assets, breaking.")
                break
                
            assets.extend(new_assets)
            
            meta = result.get("meta", {})
            next_page = meta.get("next_page")
            page_count += 1
            
            if page_count > 5: # Safety break for test
                print("✋ Stopping test at 5 pages to save time/quota.")
                break
                
        return assets

# --- TEST RUNNER ---

# Only check this if API Key exists
if os.environ.get("BRANDFOLDER_API_KEY"):
    try:
        api = BrandfolderAPI()
        bfs = api.get_brandfolders()
        if bfs:
            bf_id = bfs[0]['id']
            print(f"✅ Testing on Brandfolder: {bf_id}")
            
            # Use small per_page to FORCE pagination behavior
            print("\n--- TEST: Fetching with per_page=10 ---")
            assets = api.get_assets(brandfolder_id=bf_id, per_page=10, include_attachments=False)
            print(f"📦 Total fetched: {len(assets)}")
            
            if len(assets) > 10:
                print("✅ PASSED: Retrieved more than single page limit.")
            else:
                print("⚠️ FAILED/UNCERTAIN: Retrieved exactly 10 or fewer.")
        else:
            print("❌ No Brandfolders found.")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
else:
    print("❌ No API Key in env.")
