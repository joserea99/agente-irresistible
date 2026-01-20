from browser_service import BrowserService
import os

def test_login_flow():
    print("Testing Login Flow...")
    service = BrowserService()
    
    # Check if credentials work
    success = service.login("jose.rea@lbne.org", "jajciX-pohto7-dyd")
    
    if success:
        print("✅ Login SUCCESS! Auth state saved.")
        if os.path.exists("auth_state.json"):
             print("✅ auth_state.json created.")
    else:
        print("❌ Login FAILED.")

if __name__ == "__main__":
    test_login_flow()
