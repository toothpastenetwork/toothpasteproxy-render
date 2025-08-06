import requests
from bs4 import BeautifulSoup
from .browser import get_page
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

BLOCKED_TYPES = [
    "image", "stylesheet", "font", "media", "websocket", "xhr", "fetch", "ping", "manifest", "other"
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
        page = await get_page()

        # Block unnecessary resources
        await page.route("**/*", lambda route, req: (
            route.abort() if req.resource_type in BLOCKED_TYPES else route.continue_()
        ))

        try:
            await asyncio.wait_for(
                page.goto(url, wait_until="load", timeout=10000),
                timeout=4.0  # bail out early if loading is too slow
            )
        except asyncio.TimeoutError:
            print("[WARN] Page took too long. Returning partial content...")

        return await page.content()
