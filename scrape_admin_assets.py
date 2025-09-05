#!/usr/bin/env python3
"""
FreeWorld Admin Portal Asset Scraper
Grabs all visual assets (CSS, fonts, images, icons) from admin.freeworld.org
"""
import asyncio
import re
import os
import pathlib
import urllib.parse
import hashlib
import json
from playwright.async_api import async_playwright

# Configuration
START_URLS = [
    "https://admin.freeworld.org/login?redirect_url=https%3A%2F%2Fadmin.freeworld.org%2F",
    "https://admin.freeworld.org/"
]
OUT_DIR = pathlib.Path("scraped_assets")
ALLOWED_HOSTS = {
    "admin.freeworld.org", 
    "fonts.googleapis.com", 
    "fonts.gstatic.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com"
}

# Asset types to save
SAVE_EXTENSIONS = {
    ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".gif",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json", ".js"
}

# Regex to find URL references in CSS
CSS_URL_RE = re.compile(r"url\((?!data:)\s*['\"]?([^'\")]+)['\"]?\s*\)", re.IGNORECASE)

def sanitize_path(url: str) -> pathlib.Path:
    """Build a stable local path based on host + path + query hash"""
    try:
        u = urllib.parse.urlparse(url)
        host = u.netloc or "localhost"
        path = u.path or "/index"
        
        # Handle query parameters with hash
        qhash = ""
        if u.query:
            qhash = "-" + hashlib.sha1(u.query.encode()).hexdigest()[:8]
        
        # Extract filename and extension
        path_obj = pathlib.Path(path)
        filename = path_obj.name or "index"
        ext = path_obj.suffix
        
        if not ext:
            # Guess extension from content or URL
            lower_path = path.lower()
            if any(x in lower_path for x in ['.css', 'style']):
                ext = '.css'
            elif any(x in lower_path for x in ['.js', 'script']):
                ext = '.js'
            elif any(x in lower_path for x in ['font', '.woff', '.ttf']):
                ext = '.woff2'
            else:
                ext = '.bin'
        
        # Clean directory structure
        clean_dir = OUT_DIR / host / path_obj.parent.relative_to("/")
        clean_dir.mkdir(parents=True, exist_ok=True)
        
        # Build final filename
        stem = filename[:-len(path_obj.suffix)] if path_obj.suffix else filename
        return clean_dir / f"{stem}{qhash}{ext}"
    
    except Exception as e:
        # Fallback to simple hash-based naming
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        return OUT_DIR / f"asset_{url_hash}.bin"

async def fetch_and_save(session, url: str, saved: set, asset_map: dict):
    """Fetch URL and save to local file, recursively handling CSS imports"""
    if url in saved:
        return
    
    try:
        u = urllib.parse.urlparse(url)
        if u.netloc and u.netloc not in ALLOWED_HOSTS:
            print(f"⚠️  Skipping external host: {u.netloc}")
            return
        
        print(f"📥 Fetching: {url}")
        response = await session.get(url)
        
        if not response.ok:
            print(f"❌ Failed to fetch {url}: {response.status}")
            return
        
        data = await response.body()
        local_path = sanitize_path(url)
        local_path.write_bytes(data)
        
        saved.add(url)
        asset_map[url] = str(local_path.relative_to(OUT_DIR))
        
        print(f"✅ Saved: {local_path}")
        
        # If CSS, extract and fetch nested URLs
        content_type = response.headers.get("content-type", "").lower()
        if "text/css" in content_type or url.endswith('.css'):
            try:
                css_text = data.decode("utf-8", errors="ignore")
                nested_urls = CSS_URL_RE.findall(css_text)
                
                for nested_url in nested_urls:
                    # Resolve relative URLs
                    absolute_url = urllib.parse.urljoin(url, nested_url)
                    await fetch_and_save(session, absolute_url, saved, asset_map)
                    
            except Exception as e:
                print(f"⚠️  Error parsing CSS from {url}: {e}")
                
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")

def rewrite_css_urls(css_content: str, asset_map: dict, base_url: str) -> str:
    """Rewrite CSS url() references to use local asset paths"""
    def replace_url(match):
        original_url = match.group(1)
        absolute_url = urllib.parse.urljoin(base_url, original_url)
        
        if absolute_url in asset_map:
            local_path = asset_map[absolute_url]
            return f'url("../scraped_assets/{local_path}")'
        return match.group(0)  # Keep original if not found
    
    return CSS_URL_RE.sub(replace_url, css_content)

async def main():
    """Main scraping function"""
    print("🚀 Starting FreeWorld Admin Portal asset scraper...")
    
    # Clean output directory
    if OUT_DIR.exists():
        import shutil
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    
    saved_urls = set()
    asset_map = {}  # url -> local_path mapping
    
    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Enable request interception to capture all network requests
        intercepted_urls = set()
        
        async def handle_request(request):
            url = request.url
            parsed = urllib.parse.urlparse(url)
            
            # Check if it's an asset we want
            if (parsed.netloc in ALLOWED_HOSTS and 
                any(url.lower().endswith(ext) for ext in SAVE_EXTENSIONS)):
                intercepted_urls.add(url)
        
        page.on("request", handle_request)
        
        session = context.request
        
        # Visit each start URL
        for start_url in START_URLS:
            print(f"📄 Loading page: {start_url}")
            
            try:
                # Try with load first, fallback to domcontentloaded
                try:
                    await page.goto(start_url, wait_until="load", timeout=15000)
                except:
                    print(f"⚠️  Load timeout, trying domcontentloaded...")
                    await page.goto(start_url, wait_until="domcontentloaded", timeout=10000)
                
                await page.wait_for_timeout(3000)  # Wait for dynamic content
                
                # Extract URLs from DOM
                dom_assets = await page.evaluate("""
                () => {
                    const urls = new Set();
                    
                    // CSS links
                    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                        if (link.href) urls.add(link.href);
                    });
                    
                    // Images
                    document.querySelectorAll('img[src]').forEach(img => {
                        if (img.src) urls.add(img.src);
                    });
                    
                    // Fonts and other resources from computed styles
                    const sheets = Array.from(document.styleSheets);
                    sheets.forEach(sheet => {
                        try {
                            const rules = Array.from(sheet.cssRules || []);
                            rules.forEach(rule => {
                                if (rule.style) {
                                    const text = rule.cssText;
                                    const urlMatches = text.match(/url\\([^)]+\\)/g);
                                    if (urlMatches) {
                                        urlMatches.forEach(match => {
                                            const url = match.replace(/url\\(['\"]?([^'\")]+)['\"]?\\)/, '$1');
                                            if (url.startsWith('http')) {
                                                urls.add(url);
                                            }
                                        });
                                    }
                                }
                            });
                        } catch (e) {
                            // Cross-origin stylesheets might be blocked
                        }
                    });
                    
                    return Array.from(urls);
                }
                """)
                
                # Combine intercepted and DOM-extracted URLs
                all_urls = intercepted_urls | set(dom_assets)
                print(f"🔍 Found {len(all_urls)} potential assets")
                
                # Fetch all assets
                for url in all_urls:
                    await fetch_and_save(session, url, saved_urls, asset_map)
                    
            except Exception as e:
                print(f"❌ Error loading {start_url}: {e}")
        
        print("🔧 Post-processing CSS files...")
        
        # Post-process CSS files to rewrite URLs
        for url, local_path in asset_map.items():
            if url.endswith('.css'):
                full_path = OUT_DIR / local_path
                if full_path.exists():
                    try:
                        css_content = full_path.read_text(encoding='utf-8', errors='ignore')
                        rewritten_css = rewrite_css_urls(css_content, asset_map, url)
                        full_path.write_text(rewritten_css, encoding='utf-8')
                        print(f"✅ Rewritten CSS: {local_path}")
                    except Exception as e:
                        print(f"⚠️  Error rewriting CSS {local_path}: {e}")
        
        await browser.close()
    
    # Write manifest files
    manifest_path = OUT_DIR / "asset_manifest.json"
    manifest_data = {
        "scraped_urls": list(saved_urls),
        "asset_mapping": asset_map,
        "total_assets": len(saved_urls)
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"📋 Asset manifest written to: {manifest_path}")
    print(f"🎉 Scraping complete! Saved {len(saved_urls)} assets to {OUT_DIR}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"💥 Scraping failed: {e}")
        raise