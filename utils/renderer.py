import requests
from .browser import get_browser
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

def fetch_with_requests(url):
    """Try fetching page content via requests"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

def is_content_incomplete(html):
    """Detect if content is dynamically rendered"""
    soup = BeautifulSoup(html, "html.parser")

    # If body is empty, or canvas tag is present, likely dynamic
    body = soup.body
    if not body or not body.find_all():
        return True
    if soup.find("canvas") or soup.find("script", string=lambda s: s and "WebGL" in s):
        return True

    return False

async def render_page(url):
    try:
        html = fetch_with_requests(url)
        if is_content_incomplete(html):
            raise Exception("Incomplete content, fallback required.")
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
