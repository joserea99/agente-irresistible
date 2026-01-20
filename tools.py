from langchain_core.tools import tool
from rag_manager import RAGManager
from browser_service import BrowserService
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

@tool
def get_youtube_transcript(url: str) -> str:
    """Extracts the transcript/captions from a YouTube video URL. Use this when the user shares a YouTube link."""
    print(f"🎥 Fetching transcript for: {url}")
    try:
        # Extract video ID
        parsed_url = urlparse(url)
        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        else:
            video_id = parse_qs(parsed_url.query)['v'][0]
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        
        # Combine text
        full_text = " ".join([t['text'] for t in transcript_list])
        
        return f"Transcript for {url}:\n{full_text[:15000]}" # Limit to preventing context overflow
            
    except Exception as e:
        return f"Error extracting transcript: {e} (Note: Video must have captions enabled)"

@tool
def search_knowledge_base(query: str) -> str:
    """Searches the internal knowledge base (PDFs, crawled pages) for relevant information."""
    print(f"🕵️ Searching Knowledge Base for: {query}")
    rag = RAGManager()
    results = rag.search(query, n_results=3)
    if not results:
        return "No relevant information found in the knowledge base."
    return results

@tool
def browse_live_page(url: str) -> str:
    """Visits a live URL to read its content. Use this when the user provides a link."""
    print(f"🌍 Browsing live page: {url}")
    browser = BrowserService()
    # Ensure state/login if needed, but primarily just read the page
    # Using scrape_page which creates a fresh context
    data, error = browser.scrape_page(url)
    
    if error:
        return f"Error browsing page: {error}"
    
    return f"Title: {data['title']}\n\nContent: {data['content'][:5000]}" # Limit context
