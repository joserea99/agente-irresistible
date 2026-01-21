#!/usr/bin/env python3
"""
🧠 BRAIN BUILDER SCRIPT
Crawls my.irresistible.church and ingests all content into the knowledge base.
Run this locally on your Mac, then push to Railway.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from browser_service import BrowserService
from rag_manager import RAGManager

# Configuration
START_URL = "https://my.irresistible.church/irresistiblechurchnetwork"
MAX_DEPTH = 3
MAX_PAGES = 100  # Maximum pages to crawl
LOGIN_EMAIL = "jose.rea@lbne.org"
LOGIN_PASSWORD = "jajciX-pohto7-dyd"

def main():
    print("=" * 60)
    print("🧠 IGLESIA IRRESISTIBLE - BRAIN BUILDER")
    print("=" * 60)
    print(f"📍 Starting URL: {START_URL}")
    print(f"🔍 Max Depth: {MAX_DEPTH}")
    print(f"📄 Max Pages: {MAX_PAGES}")
    print("=" * 60)
    
    # Initialize RAG
    print("\n📚 Initializing Knowledge Base...")
    rag = RAGManager()
    initial_count = rag.get_stats()
    print(f"   Current documents: {initial_count}")
    
    # Initialize Browser
    print("\n🌐 Starting Browser...")
    browser = BrowserService()
    
    # Login first
    print("\n🔐 Logging in to irresistible.church...")
    login_success = browser.login(LOGIN_EMAIL, LOGIN_PASSWORD)
    if not login_success:
        print("❌ Login failed! Check credentials.")
        browser.close()
        return
    print("✅ Login successful!")
    
    # Start Crawling
    print(f"\n🕷️ Starting recursive crawl...")
    print(f"   This may take 5-10 minutes depending on the site size...\n")
    
    start_time = time.time()
    pages = browser.crawl_recursive(START_URL, max_depth=MAX_DEPTH, max_pages=MAX_PAGES)
    crawl_time = time.time() - start_time
    
    print(f"\n✅ Crawl complete in {crawl_time:.1f} seconds")
    print(f"   Found {len(pages)} pages")
    
    # Ingest into RAG
    print("\n📥 Ingesting content into Knowledge Base...")
    ingested = 0
    media_found = []
    
    for i, page in enumerate(pages):
        if page.get('content'):
            try:
                rag.add_document(
                    content=page['content'],
                    source_url=page['url'],
                    title=page.get('title', 'Unknown')
                )
                ingested += 1
                print(f"   [{i+1}/{len(pages)}] ✅ {page.get('title', 'Page')[:50]}...")
            except Exception as e:
                print(f"   [{i+1}/{len(pages)}] ❌ Error: {e}")
        
        # Collect media links
        if page.get('media_links'):
            media_found.extend(page['media_links'])
    
    # Summary
    final_count = rag.get_stats()
    print("\n" + "=" * 60)
    print("🎉 BRAIN BUILDING COMPLETE!")
    print("=" * 60)
    print(f"📄 Pages crawled: {len(pages)}")
    print(f"📚 Documents ingested: {ingested}")
    print(f"🎬 Media files found: {len(set(media_found))}")
    print(f"🧠 Total knowledge chunks: {final_count}")
    print("=" * 60)
    
    # Media files list
    if media_found:
        print("\n🎬 Media files discovered (can be transcribed later):")
        for url in set(media_found)[:10]:  # Show first 10
            print(f"   - {url.split('/')[-1]}")
        if len(set(media_found)) > 10:
            print(f"   ... and {len(set(media_found)) - 10} more")
    
    print("\n📋 NEXT STEPS:")
    print("1. Review the crawled content in your local app")
    print("2. Run: git add -A && git commit -m 'Add pre-built knowledge base' && git push")
    print("3. Railway will deploy with the knowledge already loaded!")
    
    browser.close()
    print("\n✨ Done!")

if __name__ == "__main__":
    main()
