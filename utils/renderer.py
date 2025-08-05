import requests
from bs4 import BeautifulSoup
from .browser import get_browser

# Keywords that imply dynamic content or games
DYNAMIC_KEYWORDS = ["<canvas", "WebGL", "phaser", "unityWeb", "Babylon", "three.min.js"]

def is_dynamic_content(html):
    html_lower = html.lower()
    return any(keyword.lower() in html_lower for keyword in DYNAMIC_KEYWORDS)

async def render_page(url):
    try:
        # Attempt fast fetch with requests
        resp = requests.get(url, timeout=7, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        })
        html = resp.text

        # Use BS4 to quickly check for critical dynamic features
        if is_dynamic_content(html):
            raise ValueError("Detected dynamic content - fallback to Playwright")

        return html
    except Exception:
        # Fallback to full browser render
        browser = await get_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            return content
        finally:
            await page.close()
