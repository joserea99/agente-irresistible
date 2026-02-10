from google import genai
import os
from dotenv import load_dotenv

load_dotenv("/Users/joserea/irresistible_agent/.env")
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ No API Key found")
else:
    client = genai.Client(api_key=api_key)
    print("🔎 Listing available models...")
    try:
        # Pager object, iterate through it
        for m in client.models.list():
            # semantic filter
            if "embedContent" in (m.supported_generation_methods or []):
                print(f"✅ Embedding Model: {m.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
