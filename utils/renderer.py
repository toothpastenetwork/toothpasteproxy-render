import requests
from bs4 import BeautifulSoup
from utils.browser import get_browser_context

def needs_full_render(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")
    return len(scripts) > 1  # If it has more than 1 script, use full JS render

async def render_page(url: str) -> str:
    try:
        # Try static HTML fetch first
        resp = requests.get(url, timeout=3, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        html = resp.text

        if not needs_full_render(html):
            print(f"[STATIC] Served via requests: {url}")
            return html
        else:
            print(f"[JS DETECTED] Switching to Playwright: {url}")
    except Exception as e:
        print(f"[FALLBACK] requests failed, using Playwright: {e}")

    # Use Playwright for full rendering
    context = await get_browser_context()
    page = await context.new_page()

    # Stealth against bot detection
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        await page.goto(url, wait_until="networkidle", timeout=15000)
        content = await page.content()
        print(f"[BROWSER] Rendered via Playwright: {url}")
    except Exception as err:
        print(f"[ERROR] Browser render failed: {url} -> {err}")
        content = "<h2>Failed to load page</h2>"
    finally:
        await page.close()

    return content
