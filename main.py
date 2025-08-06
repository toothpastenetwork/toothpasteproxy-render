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
    full = urljoin(base_url, url)
    return "/?url=" + quote(full)

def rewrite_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # Rewriting elements
    for tag, attr in {
        "a": "href", "img": "src", "script": "src", "link": "href",
        "iframe": "src", "form": "action"
    }.items():
        for t in soup.find_all(tag):
            if t.has_attr(attr):
                t[attr] = rewrite_url(base_url, t[attr])
            if tag == "form":
                t["method"] = "get"

    # Rewrite JS-based redirects
    for script in soup.find_all("script"):
        if script.string:
            script.string = re.sub(
                r'(location\.href\s*=\s*["\'])([^"\']+)(["\'])',
                lambda m: m.group(1) + rewrite_url(base_url, m.group(2)) + m.group(3),
                script.string
            )

    # Inject proxy JS
    proxy_js = """
    <script>
    (function() {
        const base = "/?url=";
        const rewrite = u => base + encodeURIComponent(new URL(u, location.href).href);

        // Intercept links
        document.addEventListener("click", function(e) {
            const t = e.target.closest("a[href]");
            if (t && !t.href.startsWith("data:")) {
                e.preventDefault();
                window.location.href = rewrite(t.getAttribute("href"));
            }
        });

        // Patch window.open
        const origOpen = window.open;
        window.open = function(u, ...args) {
            return origOpen(rewrite(u), ...args);
        };

        // Patch push/replace state
        const origPush = history.pushState;
        const origReplace = history.replaceState;
        history.pushState = function(s, t, u) {
            return origPush.call(this, s, t, rewrite(u));
        };
        history.replaceState = function(s, t, u) {
            return origReplace.call(this, s, t, rewrite(u));
        };
    })();
    </script>
    """
    if soup.head:
        soup.head.insert(0, BeautifulSoup(proxy_js, "html.parser"))

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
