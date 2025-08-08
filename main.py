from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup
import re
from utils.renderer import render_page

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def proxy(request: Request):
    target = request.query_params.get("url")
    if not target:
        return "<h2>Proxy online — use ?url=https://example.com</h2>"

    target = unquote(target.strip())
    try:
        html = await render_page(target)
        rewritten = rewrite_html(html, target)
        return HTMLResponse(content=rewritten, media_type="text/html")
    except Exception as e:
        return HTMLResponse(content=f"<pre>Proxy error:\n{e}</pre>", media_type="text/html")


def rewrite_url(base_url, url):
    if not url or url.startswith(("data:", "javascript:")):
        return url
    full = urljoin(base_url, url)
    return "/?url=" + quote(full)


def rewrite_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # Basic tag rewrites
    for tag, attr in {
        "a": "href", "img": "src", "script": "src", "link": "href",
        "iframe": "src", "form": "action"
    }.items():
        for t in soup.find_all(tag):
            if t.has_attr(attr):
                t[attr] = rewrite_url(base_url, t[attr])
            if tag == "form":
                t["method"] = "get"

    # Rewrite inline JS redirects
    for script in soup.find_all("script"):
        if script.string:
            script.string = re.sub(
                r'(location\.href\s*=\s*["\'])([^"\']+)(["\'])',
                lambda m: m.group(1) + rewrite_url(base_url, m.group(2)) + m.group(3),
                script.string
            )

    # Inject fallback CORS proxy JS
    inject_script = f"""
<script>
(function() {{
    const proxy = '/?url=';
    const rewrite = (u) => proxy + encodeURIComponent(new URL(u, '{base_url}').href);

    window.fetch = new Proxy(window.fetch, {{
        apply(target, thisArg, args) {{
            return target(...args).catch(err => {{
                const url = args[0];
                if (typeof url === 'string' && !url.startsWith(proxy)) {{
                    return target(rewrite(url), args[1]);
                }}
                throw err;
            }});
        }}
    }});

    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {{
        try {{
            return origOpen.call(this, method, url, ...rest);
        }} catch {{
            return origOpen.call(this, method, proxy + encodeURIComponent(url), ...rest);
        }}
    }};
}})();
</script>
"""
    if soup.head:
        soup.head.insert(0, BeautifulSoup(inject_script, "html.parser"))

    return str(soup)
