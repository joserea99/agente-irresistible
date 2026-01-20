from playwright.sync_api import sync_playwright
import os
import time

# File to store session cookies/storage
STORAGE_STATE = "auth_state.json"
BASE_URL = "https://my.irresistible.church/irresistiblechurchnetwork"

class BrowserService:
    def __init__(self):
        self.headless = True
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_browser(self):
        """Starts a persistent browser session."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # Load state if exists, otherwise new context
        if os.path.exists(STORAGE_STATE):
            self.context = self.browser.new_context(storage_state=STORAGE_STATE)
        else:
            self.context = self.browser.new_context()
            
        self.page = self.context.new_page()

    def login(self, username, password):
        """Performs login and saves state."""
        # Ensure browser is running
        if not self.page:
            self.start_browser()

        try:
            self.page.goto(BASE_URL)
            
            # Check if login is needed
            if "sign_in" in self.page.url:
                print("Logging in...")
                self.page.fill("#session_email", username)
                self.page.fill("#session_password", password)
                
                # Try to find the button more robustly
                try:
                    self.page.click("input[type='submit']", timeout=2000)
                except:
                    self.page.click("button:has-text('Log in')", timeout=2000)

                self.page.wait_for_load_state("networkidle")
            
            # Save storage state
            self.context.storage_state(path=STORAGE_STATE)
            print(f"Login successful. State saved to {STORAGE_STATE}")
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def get_page_content(self):
        """Extracts main content and media links from the current page."""
        if not self.page:
            return None
        title = self.page.title()
        content = self.page.inner_text("body")
        
        # Extract Media Links (MP4, MP3)
        media_links = self.page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a'));
            const media = [];
            const regex = /\.(mp4|mp3|mov|wav|m4a)$/i;
            
            links.forEach(a => {
                if (regex.test(a.href)) {
                    media.push(a.href);
                }
            });
            
            // Also check video/audio tags
            document.querySelectorAll('video, audio').forEach(el => {
                if (el.src) media.push(el.src);
                el.querySelectorAll('source').forEach(s => {
                    if (s.src) media.push(s.src);
                });
            });
            
            return [...new Set(media)];
        }""")
        
        return {"title": title, "content": content, "url": self.page.url, "media_links": media_links}

    def crawl_recursive(self, start_url, max_depth=2, max_pages=10):
        """
        Recursively crawls pages. Requires start_browser() to be called first to load auth state.
        """
        if not self.page:
             self.start_browser()

        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        results = []
        
        count = 0
        base_domain = start_url.split('/')[2] 

        while to_visit and count < max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            if depth > max_depth:
                continue

            print(f"🕷️ Crawling: {current_url} (Depth: {depth})")
            
            try:
                self.page.goto(current_url, timeout=15000)
                time.sleep(1) # Polite delay
                
                content = self.get_page_content()
                if content:
                    results.append(content)
                    count += 1
                
                if depth < max_depth:
                    links = self.page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
                    for link in links:
                        if base_domain in link and link not in visited and "logout" not in link.lower():
                            if link.startswith("http"):
                                to_visit.append((link, depth + 1))
                                
            except Exception as e:
                print(f"❌ Error crawling {current_url}: {e}")
                
        return results

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None

