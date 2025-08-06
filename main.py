from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from urllib.parse import urljoin, quote, unquote
from utils.cache import get_or_render_cached
from utils.browser import get_browser
from bs4 import BeautifulSoup
import re
import asyncio

app = FastAPI()

PREWARM_URLS = [
    "https://example.com",
    "https://en.wikipedia.org/wiki/Main_Page",
]

@app.on_event("startup")
async def warm_up():
    await get_browser()
    print("✅ Browser warmed.")
    for url in PREWARM_URLS:
        asyncio.create_task(get_or_render_cached(url))

def rewrite_url(base_url, url):
    if not url or url.startswith(("data:", "javascript:")):
        return url
    return "/?url=" + quote(urljoin(base_url, url))

def rewrite_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag, attr in {
        "a": "href", "img": "src", "script": "src", "link": "href",
        "iframe": "src", "form": "action"
    }.items():
        for t in soup.find_all(tag):
            if t.has_attr(attr):
                t[attr] = rewrite_url(base_url, t[attr])
            if tag == "form":
                t["method"] = t.get("method", "get").lower()

    for script in soup.find_all("script"):
        if script.string:
            script.string = re.sub(
                r'(location\.href\s*=\s*["\'])([^"\']+)(["\'])',
                lambda m: m.group(1) + rewrite_url(base_url, m.group(2)) + m.group(3),
                script.string
            )
    return str(soup)

@app.get("/", response_class=HTMLResponse)
async def proxy(request: Request):
    target = request.query_params.get("url")
    if not target:
        return "<h2>The proxy is online. Use ?url=https://example.com</h2>"

    target = unquote(target)
    try:
        html = await get_or_render_cached(target)
        rewritten = rewrite_html(html, target)
        return HTMLResponse(content=rewritten, media_type="text/html")
    except Exception as e:
        return HTMLResponse(content=f"<pre>Proxy error:\n{e}</pre>", media_type="text/html")
