
import os
import sys

# Need supabase installed, might run from venv
try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase library: `pip install supabase`")
    sys.exit(1)

from dotenv import load_dotenv

# load backend .env
load_dotenv("/Users/joserea/irresistible_agent/backend/.env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

if not url:
    # Fallback to frontend public one if not found in backend env
    url = "https://yuovxnpoolxwucsdvcsn.supabase.co"
    # Anonym key from frontend file
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl1b3Z4bnBvb2x4d3Vjc2R2Y3NuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NTc1OTQsImV4cCI6MjA4NjAzMzU5NH0._OYFzEnE3s9PgUPn18TR4ILnxd19_XurmCzmbr5YdBE"

print(f"Connecting to: {url}")
supabase: Client = create_client(url, key)

def check_login():
    # Ask user for input interactively if possible, but safer to hardcode for this script or use args
    if len(sys.argv) < 3:
        print("Usage: python debug_login.py <email> <password>")
        return

    email = sys.argv[1]
    password = sys.argv[2]
    
    print(f"Testing login for: {email}")
    try:
        data = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        print("✅ Login Successful!")
        user = data.user
        if user:
            print(f"User ID: {user.id}")
            print(f"Email Confirmed At: {user.email_confirmed_at}")
            
            if not user.email_confirmed_at:
                print("⚠️ WARNING: Email confirmed_at is None/Empty?")
        
        if data.session:
            print("Session Active.")
            
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        err_str = str(e)
        if "Email not confirmed" in err_str:
            print("👉 DIAGNOSIS: User hasn't clicked the confirmation link in their email.")
        elif "Invalid login credentials" in err_str:
             print("👉 DIAGNOSIS: Wrong password OR account doesn't exist.")
        elif "Rate limit exceeded" in err_str:
             print("👉 DIAGNOSIS: Too many login attempts.")

if __name__ == "__main__":
    check_login()
