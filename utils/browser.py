from playwright.async_api import async_playwright

_browser = None
_playwright = None
_page = None

async def get_browser():
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    return _browser

async def get_page():
    global _page
    browser = await get_browser()
    if _page is None:
        _page = await browser.new_page()
    return _page

async def shutdown_browser():
    global _browser, _playwright, _page
    if _page:
        await _page.close()
        _page = None
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
