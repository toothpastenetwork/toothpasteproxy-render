import requests
from bs4 import BeautifulSoup
from .browser import get_browser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

JS_KEYWORDS = [
    "React", "Next.js", "Vue", "Svelte", "Angular", "Webpack", "Canvas", "WebGL",
    "phaser", "unityWeb", "three.min.js", "pixi.min.js", "Babylon"
]

DYNAMIC_TAGS = ["canvas", "svg", "video", "webgl"]

def is_js_heavy_content(html):
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    if not body or len(body.get_text(strip=True)) < 80:
        return True
    for tag in DYNAMIC_TAGS:
        if soup.find(tag):
            return True
    scripts = soup.find_all("script")
    js_heavy = sum(1 for s in scripts if s.get("src") or s.get("type") == "module" or s.get("defer") or s.get("async"))
    if js_heavy >= 5:
        return True
    html_lower = html.lower()
    return any(keyword.lower() in html_lower for keyword in JS_KEYWORDS)

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
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return await page.content()
        finally:
            await page.close()
