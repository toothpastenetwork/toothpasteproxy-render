from .browser import get_browser

async def render_page(url):
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        return content
    finally:
        await page.close()
