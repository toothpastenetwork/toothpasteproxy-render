import requests
from bs4 import BeautifulSoup
from .browser import get_browser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

def fetch_html_with_requests(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

async def render_page(url, progress_callback=None):
    # TEMP: always use Playwright to test progress bar
    browser = await get_browser()
    page = await browser.new_page()

    if progress_callback:
        async def on_console(msg):
            if msg.type == "log":
                text = msg.text
                print(f"[Playwright Console] {text}")
                if text.startswith("__PROGRESS__:"):
                    try:
                        percent = int(text.split(":")[1])
                        await progress_callback(percent)
                        print(f"[Progress Callback] {percent}%")
                    except Exception as e:
                        print(f"[Callback Error]: {e}")
        page.on("console", on_console)

    try:
        await page.add_init_script("""
            (() => {
                console.log("📦 Injected progress script");
                let reported = 0;
                const observer = new PerformanceObserver((list) => {
                    const entries = performance.getEntriesByType("resource");
                    const total = entries.length || 50;
                    const loaded = entries.filter(e => e.responseEnd > 0).length;
                    let percent = Math.min(100, Math.round((loaded / total) * 100));
                    if (percent > reported) {
                        reported = percent;
                        console.log("__PROGRESS__:" + percent);
                    }
                });
                observer.observe({entryTypes: ["resource"]});
                console.log("✅ Progress tracker active");
            })();
        """)
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        content = await page.content()
        if progress_callback:
            await progress_callback(100)
        return content
    finally:
        await page.close()
