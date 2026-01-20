import os
import requests
import google.generativeai as genai
import tempfile
import time

# Configure Gemini
# We assume GOOGLE_API_KEY is set in env
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def download_file(url, cookies=None):
    """Downloads a file from a URL to a temporary path."""
    print(f"⬇️ Downloading media from {url}...")
    try:
        # Stream download to avoid memory issues
        with requests.get(url, stream=True, cookies=cookies) as r:
            r.raise_for_status()
            
            # Create a temp file
            # We try to guess extension or default to .mp4/.mp3
            ext = ".mp4"
            if ".mp3" in url: ext = ".mp3"
            if ".mov" in url: ext = ".mov"
            if ".wav" in url: ext = ".wav"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                return tmp_file.name
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return None

def transcribe_media_with_gemini(file_path):
    """Uploads file to Gemini and requests transcription."""
    print(f"🧠 Transcribing {file_path} with Gemini...")
    try:
        # 1. Upload file
        video_file = genai.upload_file(path=file_path)
        print(f"✅ Uploaded to Gemini: {video_file.uri}")
        
        # 2. Wait for processing (state active)
        while video_file.state.name == "PROCESSING":
            print("⏳ Processing in Gemini...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            return "Error: Gemini failed to process file."

        # 3. Generate Content
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        prompt = "Listen/Watch this media carefully. Provide a detailed transcription and summary of the content. Extract key insights, biblical references, and leadership principles. Format as Markdown."
        
        response = model.generate_content([video_file, prompt])
        
        # 4. Cleanup Gemini file (optional but good practice)
        genai.delete_file(video_file.name)
        
        return response.text

    except Exception as e:
        return f"❌ Transcription Error: {e}"
    finally:
        # Cleanup local file
        if os.path.exists(file_path):
            os.remove(file_path)

def process_media_url(url, cookies=None):
    """Orchestrates the download and transcription."""
    file_path = download_file(url, cookies)
    if not file_path:
        return "Failed to download media."
    
    transcript = transcribe_media_with_gemini(file_path)
    return transcript
