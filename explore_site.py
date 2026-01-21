#!/usr/bin/env python3
"""
🔍 SITE EXPLORER
Explores the irresistible.church site to find where the actual content is.
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from browser_service import BrowserService

def main():
    print("🔍 Exploring irresistible.church structure...")
    
    browser = BrowserService()
    browser.headless = False  # Show browser for debugging
    
    # Login
    print("🔐 Logging in...")
    browser.login("jose.rea@lbne.org", "jajciX-pohto7-dyd")
    print("✅ Logged in!")
    
    # Navigate to main dashboard
    main_url = "https://my.irresistible.church/irresistiblechurchnetwork"
    print(f"\n📍 Navigating to: {main_url}")
    browser.page.goto(main_url)
    browser.page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Get all links on the page
    print("\n🔗 Finding all links...")
    links = browser.page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText.substring(0, 50)}))")
    
    print(f"   Found {len(links)} links:")
    for link in links[:30]:  # Show first 30
        if link['href'] and 'irresistible' in link['href']:
            print(f"   - {link['text']}: {link['href']}")
    
    # Look for collection/asset links (Brandfolder specific)
    print("\n📂 Looking for collections/sections...")
    sections = browser.page.eval_on_selector_all("[class*='collection'], [class*='section'], [class*='folder']", 
        "elements => elements.map(e => ({class: e.className, text: e.innerText.substring(0, 100)}))")
    
    for section in sections[:20]:
        print(f"   - {section['class']}: {section['text'][:50]}...")
    
    # Get page title and main content areas
    print("\n📄 Main content areas:")
    content = browser.page.inner_text("body")
    print(f"   Page length: {len(content)} characters")
    print(f"   First 500 chars:\n{content[:500]}")
    
    # Check for iframes (Brandfolder often uses these)
    iframes = browser.page.eval_on_selector_all("iframe", "elements => elements.map(e => e.src)")
    if iframes:
        print(f"\n📹 Found {len(iframes)} iframes:")
        for iframe in iframes:
            print(f"   - {iframe}")
    
    # Don't close - let user see
    input("\nPress Enter to close browser...")
    browser.close()

if __name__ == "__main__":
    main()
