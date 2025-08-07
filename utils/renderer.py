import requests
from bs4 import BeautifulSoup
from utils.browser import get_browser_context

def is_js_heavy(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", src=True)
    iframes = soup.find_all("iframe", src=True)
    return (
        len(scripts) + len(iframes) >= 2 or
        "webpack" in html or
        "polyfill" in html or
        "googletag" in html or
        "data-reactroot" in html or
        "application/ld+json" in html
    )

async def render_page(url: str) -> str:
    try:
        resp = requests.get(url, timeout=4, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        html = resp.text
        if not is_js_heavy(html):
            print(f"[STATIC] Loaded fast via requests: {url}")
            return html
        else:
            print(f"[BROWSER] Switching to browser for JS-heavy page: {url}")
    except Exception as e:
        print(f"[FALLBACK] Requests failed, switching to browser: {e}")

    context = await get_browser_context()
    page = await context.new_page()

    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    await page.route("**/*", lambda route, req: route.continue_())

    try:
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        print(f"[RENDERED] Loaded via Playwright: {url}")
    except Exception as err:
        print(f"[ERROR] Failed to render via browser: {url}\n{err}")
        content = "<h2>Failed to load page</h2>"
    finally:
        await page.close()

    return content
