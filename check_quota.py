
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("No API Key found")
    exit()

genai.configure(api_key=api_key)

print("🔍 Scanning Gemini Storage...")
files = list(genai.list_files())
total_files = len(files)
print(f"📉 Found {total_files} files in storage.")

# Calculate roughly (meta usually doesn't show size in list, but we can verify existence)
if total_files > 0:
    print("Sample files:")
    for f in files[:5]:
        print(f" - {f.name} ({f.display_name}) - State: {f.state.name}")
else:
    print("Storage is empty.")
