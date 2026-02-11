
import os
from google import genai
from google.genai import types
from fastapi import HTTPException
import time

class MediaService:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            print("❌ Warning: GOOGLE_API_KEY not set. Media transcription will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            
    def transcribe_media(self, file_path: str, mime_type: str) -> str:
        """
        Uploads an audio/video file to Gemini and retrieves the transcription.
        """
        if not self.client:
             raise ValueError("GOOGLE_API_KEY not configured.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            print(f"📤 Uploading media to Gemini: {file_path} ({mime_type})")
            
            # Upload file using new SDK
            # The new SDK handles upload and processing wait more gracefully in some versions,
            # but we'll stick to the standard upload pattern.
            media_file = self.client.files.upload(file=file_path)
            
            # Wait for processing state
            attempts = 0
            MAX_ATTEMPTS = 60 # 2 minutes max (2s sleep * 60)
            
            while media_file.state.name == "PROCESSING":
                print(f"⏳ Processing media file... ({attempts}/{MAX_ATTEMPTS})", end="\r")
                time.sleep(2)
                media_file = self.client.files.get(name=media_file.name)
                attempts += 1
                
                if attempts > MAX_ATTEMPTS:
                    raise TimeoutError("Media processing timed out in Gemini (Server Side).")
                
            if media_file.state.name == "FAILED":
                raise ValueError("Media processing failed in Gemini.")
                
            print(f"✅ Media ready: {media_file.uri}")
            
            prompt = "Transcribe the audio in this file. Provide a comprehensive summary of the key points, followed by a detailed transcript if possible. If it's a video, describe the visual content as well."
            
            # Model Fallback Strategy
            models_to_try = [
                "gemini-2.0-flash",      # New standard, very fast
                "gemini-1.5-flash",      # Good fallback
                "gemini-1.5-pro",        # High quality fallback
            ]
            
            response = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    print(f"🤖 Trying Gemini Model: {model_name}...")
                    
                    # Generate content with new SDK
                    # contents accepts text and file objects/references
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[prompt, media_file]
                    )
                    
                    if response and response.text:
                        print(f"✅ Success with model: {model_name}")
                        break
                except Exception as e:
                    print(f"⚠️ Model {model_name} failed: {e}")
                    last_error = e
                    continue
            
            if not response or not response.text:
                 raise ValueError(f"All Gemini models failed. Last error: {last_error}")
            
            return response.text
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return f"Error transcribing media: {str(e)}"
        
        finally:
            # Clean up (delete from cloud to save space/privacy)
            if 'media_file' in locals() and media_file:
                try:
                    print(f"🗑️ Deleting remote file: {media_file.name}")
                    self.client.files.delete(name=media_file.name)
                except Exception as cleanup_e:
                    print(f"⚠️ Failed to delete processed file: {cleanup_e}")

