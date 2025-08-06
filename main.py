from quart import Quart, request, make_response, jsonify
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup
import re
import asyncio
from utils.renderer import render_page
from utils.browser import shutdown_browser
from collections import defaultdict

app = Quart(__name__)
progress_store = defaultdict(int)

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

@app.before_serving
async def startup():
    pass

@app.after_serving
async def cleanup():
    await shutdown_browser()

@app.route("/progress/<task_id>")
async def progress(task_id):
    percent = progress_store.get(task_id, 0)
    return jsonify({"progress": percent})

@app.route("/", methods=["GET"])
async def proxy():
    target = request.args.get("url")
    if not target:
        return "<h2>The proxy is online, but a link is required. Please check the URL and try again.</h2>"

    target = unquote(target)
    task_id = str(hash(target))

    # If AJAX polling
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        async def report_progress(percent):
            progress_store[task_id] = percent
            print(f"[SERVER] Progress update for {task_id}: {percent}%")

        try:
            html = await render_page(target, progress_callback=report_progress)
            rewritten = rewrite_html(html, target)
            response = await make_response(rewritten)
            response.headers["Content-Type"] = "text/html"
            return response
        except Exception as e:
            return f"<pre>Proxy error:\n{e}</pre>"

    # Otherwise: serve loading bar
    quoted = quote(target)
    loading_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rendering {target}</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 5em; }}
            .bar {{ width: 100%%; background: #ddd; height: 30px; border-radius: 4px; margin-top: 20px; }}
            .fill {{ height: 100%%; background: #4caf50; width: 0%%; transition: width 0.3s ease; }}
        </style>
    </head>
    <body>
        <h2>Rendering page…</h2>
        <div class="bar"><div class="fill" id="fill"></div></div>
        <p id="percent">0%</p>
        <script>
            console.log("[Client] Starting progress polling...");
            async function poll() {{
                try {{
                    let res = await fetch("/progress/{task_id}");
                    let data = await res.json();
                    let percent = data.progress;
                    console.log("[Client] Fetched progress:", percent);
                    document.getElementById("fill").style.width = percent + "%";
                    document.getElementById("percent").innerText = percent + "%";
                    if (percent >= 100) {{
                        console.log("[Client] Render complete. Redirecting...");
                        window.location.href = "/?url={quoted}";
                    }} else {{
                        setTimeout(poll, 500);
                    }}
                }} catch (err) {{
                    console.error("[Client] Polling failed:", err);
                    setTimeout(poll, 1000);
                }}
            }}
            poll();
        </script>
    </body>
    </html>
    """
    return await make_response(loading_html)
