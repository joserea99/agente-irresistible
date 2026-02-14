
import os
import sys

# Configure path so we can import from backend source
sys.path.append("/Users/joserea/irresistible_agent/backend")
from app.services.brandfolder_service import BrandfolderAPI

from dotenv import load_dotenv

load_dotenv()

def test_class_pagination():
    print("🚀 Testing BrandfolderAPI Class Pagination...")
    
    # Needs valid BF API key
    if not os.environ.get("BRANDFOLDER_API_KEY"):
         print("❌ No API KEY found. Set 'BRANDFOLDER_API_KEY'!")
         return
         
    try:
        api = BrandfolderAPI()
        
        print("1. Getting Brandfolders...")
        bfs = api.get_brandfolders()
        if not bfs:
            print("❌ No brandfolders found")
            return
            
        bf_id = bfs[0]['id']
        bf_name = bfs[0]['attributes']['name']
        print(f"✅ Using Brandfolder: {bf_name} ({bf_id})")
        
        # 2. Test get_assets with SMALL pagination to force next_page
        print("\n2. Testing get_assets(per_page=10)...")
        # Forcing small per_page so pagination logic triggers even with 100 assets
        # The class doesn't have per_page arg on get_assets but params is internal.
        # Wait, the method signature is: get_assets(..., per_page: int = 100)
        
        assets = api.get_assets(brandfolder_id=bf_id, per_page=10)
        
        count = len(assets)
        print(f"📦 Total Assets Returned: {count}")
        
        if count > 10:
            print("✅ Pagination WORKED! (Received more than 10 items despite per_page=10)")
            print(f"First item ID: {assets[0]['id']}")
            print(f"Last item ID: {assets[-1]['id']}")
        elif count == 10:
            print("⚠️ Pagination FAIL: Received exactly 10 items (limit). Code didn't fetch next page.")
        else:
            print(f"ℹ️ Total assets ({count}) is small, so pagination wasn't needed.")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_class_pagination()
