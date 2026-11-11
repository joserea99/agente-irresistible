from .rag_service import RAGManager
from .brandfolder_service import BrandfolderAPI
from ..core.config import settings
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs


SPANISH_TO_ENGLISH_MAP = {
    "matrimonio": "marriage",
    "matrimonios": "marriage",
    "parejas": "marriage",
    "niños": "children",
    "ninos": "children",
    "infantil": "children",
    "jóvenes": "students",
    "jovenes": "students",
    "adolescentes": "students",
    "grupos": "groups",
    "grupos pequeños": "community groups",
    "voluntarios": "volunteer",
    "voluntariado": "volunteer",
    "finanzas": "generosity",
    "dinero": "money",
    "generosidad": "be rich",
    "liderazgo": "leadership",
    "bienvenida": "guest services",
    "invitados": "guest services",
    "atención al invitado": "guest services",
    "anfitriones": "guest services",
    "alabanza": "worship",
    "música": "music",
    "musica": "music",
    "ansiedad": "anxiety",
    "perdón": "forgiveness",
    "perdon": "forgiveness",
    "familia": "family",
    "padres": "parent",
    "fe": "faith",
    "visión": "vision",
    "vision": "vision",
    "estrategia": "strategy",
}


def search_brandfolder_catalog(query: str) -> str:
    """Searches the official ministry catalog of 1,821 assets, sermon series,
    small group guides, kids curriculum, and leadership manuals.
    Use this whenever the user asks about library resources, official series, or wants to compare/analyze
    a document in light of the reference library."""
    try:
        bf = BrandfolderAPI(api_key=settings.brandfolder_api_key)
        if not bf.is_configured():
            return "Brandfolder API key is not configured."
        brandfolders = bf.get_brandfolders()
        if not brandfolders:
            return "No Brandfolder collections available."
        bf_id = brandfolders[0]["id"]
        raw_q = (query or "").strip()
        search_q = SPANISH_TO_ENGLISH_MAP.get(raw_q.lower(), raw_q)
        if search_q == raw_q:
            for es_term, en_term in SPANISH_TO_ENGLISH_MAP.items():
                if es_term in raw_q.lower():
                    search_q = en_term
                    break
        assets = bf.search_assets(bf_id, search_q, max_pages=1)
        if not assets and search_q != raw_q:
            assets = bf.search_assets(bf_id, raw_q, max_pages=1)
        if not assets:
            return f"No exact catalog assets matched '{query}'."
        lines = []
        for a in assets[:8]:
            info = bf.extract_asset_info(a)
            desc = (info.get("description") or "").replace("<p>", "").replace("</p>", " ").strip()
            lines.append(f"- **{info.get('name')}**: {desc[:300]} (URL: {info.get('url')})")
        return "Reference Library Resources found:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error searching catalog: {e}"

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
    """Searches the church's internal knowledge base (books,
    PDFs, sermons, crawled pages) for relevant information. Use this whenever the
    user asks about strategy, models, frameworks, ministry practices, or anything
    that may be documented in the church library. Returns relevant excerpts."""
    print(f"🕵️ Searching Knowledge Base for: {query}")
    rag = RAGManager()
    results = rag.search(query, n_results=5)
    if not results:
        print(f"🔄 Vector store returned no results for '{query}', falling back to live catalog search...")
        return search_brandfolder_catalog(query)
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
