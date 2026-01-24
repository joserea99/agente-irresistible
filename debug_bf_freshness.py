
import os
import requests
import time
from app.services.brandfolder_service import BrandfolderAPI

def check_freshness():
    print("🕵️‍♀️ Debugging Brandfolder URL Freshness...")
    
    api_key = os.environ.get("BRANDFOLDER_API_KEY")
    if not api_key:
        print("❌ No API Key found")
        return

    api = BrandfolderAPI(api_key)
    
    # 1. Get First Brandfolder
    bfs = api.get_brandfolders()
    if not bfs:
        print("❌ No brandfolders")
        return
    bf_id = bfs[0]['id']
    print(f"📂 Brandfolder: {bfs[0]['attributes']['name']}")
    
    # 2. Search for a video or audio
    res = api.search_assets(bf_id, "video OR audio", include_attachments=True)
    if not res:
        print("⚠️ No assets found via search")
        # Try getting any assets
        res = api.get_assets(brandfolder_id=bf_id, per_page=5)
    
    target = None
    for asset in res:
        info = api.extract_asset_info(asset)
        for att in info['attachments']:
            if 'video' in (att.get('mimetype') or '') or 'audio' in (att.get('mimetype') or ''):
                target = asset
                break
        if target:
            break
            
    if not target:
        print("❌ No video/audio assets found to test")
        return

    print(f"🎯 Target Asset: {target['id']}")
    
    # 3. Get Details URL 1
    t1 = api.extract_asset_info(api.get_asset_details(target['id']))
    url1 = t1['attachments'][0]['url']
    print(f"🔗 URL 1: {url1[:50]}... (Expires: {extract_expiry(url1)})")
    
    # 4. Wait 5 seconds
    print("⏳ Waiting 5s...")
    time.sleep(5)
    
    # 5. Get Details URL 2
    t2 = api.extract_asset_info(api.get_asset_details(target['id']))
    url2 = t2['attachments'][0]['url']
    print(f"🔗 URL 2: {url2[:50]}... (Expires: {extract_expiry(url2)})")
    
    if url1 == url2:
        print("⚠️ WARNING: URLs are IDENTICAL. Refresh might not work if cached.")
    else:
        print("✅ URLs CHANGED. Refresh triggers new signature.")
        
    # 6. Test Download of URL 2
    print("⬇️ Testing Download of URL 2...")
    path = api.download_attachment(url2)
    if path:
        print("✅ Download SUCCESS")
        os.remove(path)
    else:
        print("❌ Download FAILED")

def extract_expiry(url):
    try:
        if "Expires=" in url:
            return url.split("Expires=")[1].split("&")[0]
    except:
        pass
    return "Unknown"

if __name__ == "__main__":
    check_freshness()
