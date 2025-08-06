from playwright.async_api import async_playwright

_browser = None
_playwright = None
_browser_context = None

async def get_browser():
    global _browser, _playwright

    try:
        if _browser:
            # Test with dummy context call
            await _browser.version()  # ✅ safe test to detect crash
            return _browser
    except Exception:
        print("[RESTART] Browser appears dead. Restarting...")
        if _browser:
            try: await _browser.close()
            except: pass
        if _playwright:
            try: await _playwright.stop()
            except: pass
        _browser, _playwright = None, None

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

    try:
        if _browser_context is None or _browser_context.is_closed():
            raise Exception("Context missing or closed")
        return _browser_context
    except:
        print("[RESTART] Context was closed, restarting...")
        _browser_context = await browser.new_context(
            ignore_https_errors=True
        )
        return _browser_context
