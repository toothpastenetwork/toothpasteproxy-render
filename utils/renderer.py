import requests
from bs4 import BeautifulSoup
from .browser import get_browser_context
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

BLOCKED_TYPES = [
    "image", "stylesheet", "font", "media", "websocket", "xhr", "fetch", "ping", "manifest", "other"
]

BLOCKED_DOMAINS = [
    "googletag", "doubleclick", "facebook", "ytimg", "ads.", "tracking", "twitter", "cloudflareinsights"
]

def is_js_heavy_content(html):
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("canvas") or soup.find("webgl") or len(soup.find_all("script")) > 10:
        return True
    if not soup.body or len(soup.body.get_text(strip=True)) < 50:
        return True
    return False

def fetch_html_with_requests(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

async def render_page(url):
    try:
        html = fetch_html_with_requests(url)
        if is_js_heavy_content(html):
            raise Exception("Dynamic content detected")
        return html
    except Exception:
        context = await get_browser_context()
        page = await context.new_page()

        await page.route("**/*", lambda route, request: (
            route.abort() if (
                request.resource_type in BLOCKED_TYPES or
                any(domain in request.url for domain in BLOCKED_DOMAINS)
            ) else route.continue_()
        ))

        try:
            await asyncio.wait_for(
                page.goto(url, wait_until="load", timeout=10000),
                timeout=4.0
            )
        except asyncio.TimeoutError:
            print("[WARN] Timeout hit — returning partial content")

        content = await page.content()
        await page.close()
        return content
