from playwright.async_api import async_playwright

_browser = None
_playwright = None
_browser_context = None

async def get_browser():
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-translate",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--no-sandbox",
                "--no-zygote",
                "--single-process",
                "--disable-features=site-per-process",
                "--remote-debugging-port=0"
            ]
        )
    return _browser

async def get_browser_context():
    global _browser_context
    browser = await get_browser()
    if _browser_context is None:
        _browser_context = await browser.new_context(
            ignore_https_errors=True  # ✅ Properly placed here
        )
    return _browser_context
