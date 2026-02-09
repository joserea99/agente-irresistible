import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("/Users/joserea/irresistible_agent/.env")
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ No API Key found")
else:
    genai.configure(api_key=api_key)
    print("🔎 Listing available models...")
    try:
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                print(f"✅ Embedding Model: {m.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
