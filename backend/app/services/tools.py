from .rag_service import RAGManager
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_youtube_transcript(url: str) -> str:
    """Extracts the transcript/captions from a YouTube video URL. Use this when the user shares a YouTube link."""
    print(f"🎥 Fetching transcript for: {url}")
    try:
        # Extract video ID
        parsed_url = urlparse(url)
        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        else:
            query = parse_qs(parsed_url.query)
            if 'v' in query:
                video_id = query['v'][0]
            else:
                return "Error: Could not extract video ID from URL."
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        
        # Combine text
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return f"Transcript for {url}:\n{full_text[:15000]}" # Limit to preventing context overflow
            
    except Exception as e:
        return f"Error extracting transcript: {e} (Note: Video must have captions enabled)"

def search_knowledge_base(query: str) -> str:
    """Searches the internal knowledge base (PDFs, crawled pages) for relevant information."""
    print(f"🕵️ Searching Knowledge Base for: {query}")
    rag = RAGManager()
    results = rag.search(query, n_results=3)
    if not results:
        return "No relevant information found in the knowledge base."
    return results

def browse_live_page(url: str) -> str:
    """Visits a live URL to read its content. Use this when the user provides a link."""
    print(f"🌍 Browsing live page: {url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else "No Title"
        
        # Remove scripts and styles
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # Get text
        text = soup.get_text()
        
        # Clean text (remove excessive whitespace)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return f"Title: {title}\n\nContent: {clean_text[:5000]}" # Limit context
    
    except Exception as e:
        return f"Error browsing page: {e}"
