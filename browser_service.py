from playwright.sync_api import sync_playwright
import os
import time

# File to store session cookies/storage
STORAGE_STATE = "auth_state.json"
BASE_URL = "https://my.irresistible.church/irresistiblechurchnetwork"

# Browserless connection for cloud deployment
# Sign up at browserless.io for a free API key
BROWSERLESS_URL = os.environ.get("BROWSERLESS_URL", None)

class BrowserService:
    def __init__(self):
        self.headless = True
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_remote = False

    def start_browser(self):
        """Starts a browser session - local or remote depending on environment."""
        self.playwright = sync_playwright().start()
        
        # Check if we should use a remote browser (Browserless)
        if BROWSERLESS_URL:
            print(f"🌐 Connecting to remote browser at Browserless...")
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(BROWSERLESS_URL)
                self.is_remote = True
                print("✅ Connected to remote browser!")
            except Exception as e:
                print(f"❌ Failed to connect to Browserless: {e}")
                print("⚠️ Falling back to local browser...")
                self._start_local_browser()
        else:
            self._start_local_browser()
        
        # Create context and page
        if self.browser:
            # For remote browsers, don't use storage_state (session is fresh each time)
            if self.is_remote:
                self.context = self.browser.new_context()
            else:
                # Load state if exists for local browser
                if os.path.exists(STORAGE_STATE):
                    self.context = self.browser.new_context(storage_state=STORAGE_STATE)
                else:
                    self.context = self.browser.new_context()
            
            self.page = self.context.new_page()
    
    def _start_local_browser(self):
        """Start local Chromium browser."""
        try:
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.is_remote = False
            print("🖥️ Using local browser")
        except Exception as e:
            print(f"❌ Failed to start local browser: {e}")
            self.browser = None

    def login(self, username, password):
        """Performs login and saves state."""
        if not self.page:
            self.start_browser()
        
        if not self.browser:
            print("❌ No browser available!")
            return False
        
        self.credentials = {"username": username, "password": password}

        try:
            self.page.goto(BASE_URL, wait_until="networkidle")
            import time
            time.sleep(2)  # Let the page fully load
            
            # Check if login is needed
            if "sign" in self.page.url.lower() or "login" in self.page.url.lower():
                print("🔐 Logging in...")
                
                # Wait for form to be ready
                self.page.wait_for_selector("#session_email", timeout=10000)
                self.page.fill("#session_email", username)
                self.page.fill("#session_password", password)
                
                # Try to find the button more robustly
                try:
                    self.page.click("input[type='submit']", timeout=3000)
                except:
                    try:
                        self.page.click("button:has-text('Log in')", timeout=3000)
                    except:
                        self.page.click("button[type='submit']", timeout=3000)

                self.page.wait_for_load_state("networkidle")
                time.sleep(3)  # Wait for session to establish
                
                # Verify we're actually logged in
                if "sign" in self.page.url.lower() or "login" in self.page.url.lower():
                    print("⚠️ Still on login page - login may have failed")
                    return False
            
            # Save storage state (only for local browsers)
            if not self.is_remote:
                self.context.storage_state(path=STORAGE_STATE)
            print(f"✅ Login successful! Current URL: {self.page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def ensure_logged_in(self):
        """Re-authenticates if we've been logged out."""
        if not self.page:
            return False
        
        current_url = self.page.url
        if "sign" in current_url.lower() or "login" in current_url.lower():
            print("🔄 Session expired, re-authenticating...")
            if hasattr(self, 'credentials'):
                return self.login(self.credentials["username"], self.credentials["password"])
            return False
        return True

    def get_page_content(self):
        """
        Extracts main content and media links from the current page.
        Improved for SPA handling - waits for dynamic content to load.
        """
        if not self.page:
            return None
        
        try:
            # Wait for SPA content to load
            self._wait_for_spa_content()
            
            title = self.page.title()
            
            # Try multiple content extraction strategies for SPAs
            content = self._extract_spa_content()
            
            # Extract Media Links with improved detection
            media_links = self._extract_media_links()
            
            return {
                "title": title, 
                "content": content, 
                "url": self.page.url, 
                "media_links": media_links
            }
        except Exception as e:
            print(f"⚠️ Error extracting content: {e}")
            return {"title": "", "content": "", "url": self.page.url, "media_links": []}
    
    def _wait_for_spa_content(self):
        """Wait for SPA/dynamic content to load."""
        try:
            # Wait for network to be idle (most SPA data loaded)
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        # Additional wait for React/Angular/Vue apps
        time.sleep(2)
        
        # Try to wait for common SPA content containers
        spa_selectors = [
            "[data-testid]",           # React testing library
            "[class*='asset']",        # Brandfolder assets
            "[class*='card']",         # Card components
            "[class*='content']",      # Content areas
            "[class*='collection']",   # Collections
            "main",                    # Main content
            "[role='main']",           # ARIA main
            ".bf-asset",               # Brandfolder specific
            ".asset-item",             # Asset items
        ]
        
        for selector in spa_selectors:
            try:
                self.page.wait_for_selector(selector, timeout=3000)
                break
            except:
                continue
    
    def _extract_spa_content(self):
        """Extract content from SPA with multiple strategies."""
        content_parts = []
        
        # Strategy 1: Get visible text from main content areas
        content_selectors = [
            "main",
            "[role='main']",
            ".content",
            "#content",
            ".container",
            "[class*='asset']",
            "[class*='collection']",
        ]
        
        for selector in content_selectors:
            try:
                elements = self.page.query_selector_all(selector)
                for el in elements:
                    text = el.inner_text()
                    if text and len(text) > 50:
                        content_parts.append(text)
            except:
                continue
        
        # Strategy 2: Extract from Brandfolder-specific elements
        try:
            # Asset titles and descriptions
            asset_info = self.page.evaluate("""() => {
                const info = [];
                
                // Asset cards/tiles
                document.querySelectorAll('[class*="asset"], [class*="card"], [class*="tile"]').forEach(el => {
                    const title = el.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                    const desc = el.querySelector('p, [class*="description"], [class*="desc"]');
                    if (title) info.push('ASSET: ' + title.innerText);
                    if (desc) info.push('DESCRIPCIÓN: ' + desc.innerText);
                });
                
                // Section headers
                document.querySelectorAll('[class*="section"], [class*="folder"]').forEach(el => {
                    const header = el.querySelector('h1, h2, h3');
                    if (header) info.push('SECCIÓN: ' + header.innerText);
                });
                
                return info;
            }""")
            content_parts.extend(asset_info)
        except:
            pass
        
        # Strategy 3: Fallback to body text
        if not content_parts:
            try:
                content_parts.append(self.page.inner_text("body"))
            except:
                pass
        
        # Combine and clean
        combined = "\n\n".join(content_parts)
        # Remove excessive whitespace
        import re
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        combined = re.sub(r' {2,}', ' ', combined)
        
        return combined[:50000]  # Limit size
    
    def _extract_media_links(self):
        """Extract media links with improved detection for SPAs."""
        try:
            media_links = self.page.evaluate("""() => {
                const media = new Set();
                const mediaExtensions = /\\.(mp4|mp3|mov|wav|m4a|pdf|docx?|pptx?|webm|avi|ogg)$/i;
                
                // Standard links
                document.querySelectorAll('a').forEach(a => {
                    if (a.href && mediaExtensions.test(a.href)) {
                        media.add(a.href);
                    }
                });
                
                // Video/audio sources
                document.querySelectorAll('video, audio').forEach(el => {
                    if (el.src) media.add(el.src);
                    el.querySelectorAll('source').forEach(s => {
                        if (s.src) media.add(s.src);
                    });
                });
                
                // Data attributes (common in SPAs)
                document.querySelectorAll('[data-src], [data-url], [data-file]').forEach(el => {
                    ['data-src', 'data-url', 'data-file'].forEach(attr => {
                        const val = el.getAttribute(attr);
                        if (val && (mediaExtensions.test(val) || val.includes('download'))) {
                            media.add(val);
                        }
                    });
                });
                
                // Brandfolder-specific: download buttons/links
                document.querySelectorAll('[class*="download"], [aria-label*="download"]').forEach(el => {
                    if (el.href) media.add(el.href);
                    if (el.dataset && el.dataset.url) media.add(el.dataset.url);
                });
                
                // Background images/videos (sometimes used for previews)
                document.querySelectorAll('[style*="background"]').forEach(el => {
                    const style = el.getAttribute('style');
                    const urlMatch = style.match(/url\\(['"](.*?)['"]\\)/);
                    if (urlMatch && mediaExtensions.test(urlMatch[1])) {
                        media.add(urlMatch[1]);
                    }
                });
                
                // iframe sources (embedded content)
                document.querySelectorAll('iframe').forEach(iframe => {
                    if (iframe.src && (iframe.src.includes('video') || iframe.src.includes('audio'))) {
                        media.add(iframe.src);
                    }
                });
                
                return [...media];
            }""")
            return media_links
        except Exception as e:
            print(f"⚠️ Error extracting media: {e}")
            return []

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
