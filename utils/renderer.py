import requests
from bs4 import BeautifulSoup
from .browser import get_browser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

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
        browser = await get_browser()
        page = await browser.new_page()

        # Block images, fonts, media
        await page.route("**/*", lambda route, request: (
            route.abort() if request.resource_type in ["image", "font", "stylesheet", "media"] else route.continue_()
        ))

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            content = await page.content()
            return content
        finally:
            await page.close()
