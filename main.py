from quart import Quart, request, make_response, Response
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup
import re
from utils.renderer import render_page

app = Quart(__name__)

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

@app.route("/", methods=["GET"])
async def proxy():
    target = request.args.get("url")
    if not target:
        return "<h2>🧪 Proxy Browser Running — use ?url=https://example.com</h2>"

    target = unquote(target)
    try:
        html = await render_page(target)
        rewritten = rewrite_html(html, target)
        response = await make_response(rewritten)
        response.headers["Content-Type"] = "text/html"
        return response
    except Exception as e:
        return f"<pre>Proxy error:\n{e}</pre>"
