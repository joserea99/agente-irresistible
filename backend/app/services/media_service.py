
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
            
            # Generate content (Transcription)
            # Use explicit version to avoid 404s on aliases
            model = genai.GenerativeModel("gemini-1.5-flash-001")
            
            prompt = "Transcribe the audio in this file. Provide a comprehensive summary of the key points, followed by a detailed transcript if possible. If it's a video, describe the visual content as well."
            
            response = model.generate_content([prompt, media_file])
            
            # Clean up (delete from cloud to save space/privacy)
            # genai.delete_file(media_file.name) # Optional: uncomment if immediate cleanup is desired
            
            return response.text
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return f"Error transcribing media: {str(e)}"
