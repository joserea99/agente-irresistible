
import requests
import sys

# CONFIGURLATION
# Tentaiva de URL de producción basada en logs anteriores (User can update this)
API_URL = "https://web-production-7054f.up.railway.app" 
EMAIL = "tester3@example.com"
PASSWORD = "pass"

def log(msg):
    print(f"[VERIFY] {msg}")

def login():
    log(f"🔐 Logging in to {API_URL}...")
    try:
        response = requests.post(f"{API_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD})
        
        if response.status_code == 401:
            log("❌ Login Failed: Invalid Credentials")
            return None
            
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        log(f"❌ Login Error: {e}")
        return None

def check_history(token):
    headers = {"Authorization": f"Bearer {token}"}
    log("📜 Fetching search history...")
    try:
        response = requests.get(f"{API_URL}/brandfolder/research/history", params={"username": EMAIL}, headers=headers)
        response.raise_for_status()
        
        sessions = response.json()
        if not sessions:
            log("⚠️ No research sessions found.")
            return None
            
        # Get latest
        latest = sessions[0]
        log(f"🔎 Latest Session: '{latest['query']}' (ID: {latest['id']})")
        log(f"   Status: {latest['status']}")
        return latest['id']
        
    except Exception as e:
        log(f"❌ Failed to get history: {e}")
        return None

def inspect_session(token, session_id):
    headers = {"Authorization": f"Bearer {token}"}
    log(f"🕵️ Inspecting assets for session {session_id}...")
    
    try:
        response = requests.get(f"{API_URL}/brandfolder/research/{session_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        assets = data.get("assets", [])
        log(f"📦 Found {len(assets)} assets.")
        
        transcribed_count = 0
        video_count = 0
        
        print("\n--- SAMPLE ASSETS ---")
        for asset in assets: 
            status = asset.get('status', 'unknown')
            content = asset.get('content') or ""
            type_ = asset.get('type')
            
            has_transcript = "--- TRANSCRIPT ---" in content or "TRANSCRIPTION" in content
            
            if type_ in ['video', 'video/mp4'] or 'video' in type_:
                video_count += 1
                if has_transcript:
                    transcribed_count += 1
                    print(f"✅ [VIDEO] {asset['name']} (Has Transcript!)")
                else:
                    print(f"⚠️ [VIDEO] {asset['name']} (No Transcript - Status: {status})")

        print("\n--- RESULTS ---")
        if video_count > 0:
            if transcribed_count > 0:
                print(f"✅ SUCCESS: {transcribed_count}/{video_count} videos have transcripts.")
            else:
                print(f"❌ FAILURE: 0/{video_count} videos have transcripts.")
        else:
            print("ℹ️ No video assets found in this session.")
            
    except Exception as e:
        log(f"❌ Failed to inspect session: {e}")

if __name__ == "__main__":
    token = login()
    if token:
        sid = check_history(token)
        if sid:
            inspect_session(token, sid)
