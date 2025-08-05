import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .browser import get_browser
from functools import lru_cache

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

JS_HEAVY_DOMAINS = [
    "itch.io", "crazygames.com", "github.io", "unity.com", "babylonjs.com"
]

def is_js_heavy(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    return any(js_domain in domain for js_domain in JS_HEAVY_DOMAINS)

@lru_cache(maxsize=100)
def cached_static_render(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

async def render_page(url):
    if is_js_heavy(url):
        # Heavy site — go full browser
        browser = await get_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            return await page.content()
        finally:
            await page.close()

    # Fast path — use cache if possible
    try:
        return cached_static_render(url)
    except Exception:
        # fallback only if request fails (e.g., 403, JS redirect)
        browser = await get_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            return await page.content()
        finally:
            await page.close()
