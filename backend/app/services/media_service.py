
import os
import google.generativeai as genai
from fastapi import HTTPException
import time

class MediaService:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Warning: GOOGLE_API_KEY not set. Media transcription will fail.")
        else:
            genai.configure(api_key=api_key)
            
    def transcribe_media(self, file_path: str, mime_type: str) -> str:
        """
        Uploads an audio/video file to Gemini and retrieves the transcription.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            print(f"📤 Uploading media to Gemini: {file_path} ({mime_type})")
            
            # Upload file
            media_file = genai.upload_file(path=file_path, mime_type=mime_type)
            
            # Wait for processing state
            attempts = 0
            MAX_ATTEMPTS = 60 # 2 minutes max (2s sleep * 60)
            
            while media_file.state.name == "PROCESSING":
                print(f"⏳ Processing media file... ({attempts}/{MAX_ATTEMPTS})", end="\r")
                time.sleep(2)
                media_file = genai.get_file(media_file.name)
                attempts += 1
                
                if attempts > MAX_ATTEMPTS:
                    raise TimeoutError("Media processing timed out in Gemini.")
                
            if media_file.state.name == "FAILED":
                raise ValueError("Media processing failed in Gemini.")
                
            print(f"✅ Media ready: {media_file.uri}")
            
            # Model Fallback Strategy
            # The library/API version might vary, so we try multiple known aliases
            models_to_try = [
                "gemini-1.5-flash",
                "gemini-1.5-flash-001",
                "gemini-1.5-pro",
                "gemini-1.5-pro-001",
                "gemini-pro-vision" # Last resort for older envs (Supports video)
            ]
            
            response = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    print(f"🤖 Trying Gemini Model: {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([prompt, media_file])
                    print(f"✅ Success with model: {model_name}")
                    break
                except Exception as e:
                    print(f"⚠️ Model {model_name} failed: {e}")
                    last_error = e
                    continue
            
            if not response:
                raise ValueError(f"All Gemini models failed. Last error: {last_error}")
            
            # Clean up (delete from cloud to save space/privacy)
            # genai.delete_file(media_file.name) # Optional: uncomment if immediate cleanup is desired
            
            return response.text
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return f"Error transcribing media: {str(e)}"
