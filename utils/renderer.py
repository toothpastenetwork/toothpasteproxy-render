async def render_page(url, progress_callback=None):
    try:
        html = fetch_html_with_requests(url)
        if is_js_heavy_content(html):
            raise Exception("Dynamic content detected")
        if progress_callback:
            await progress_callback(100)
        return html
    except Exception:
        browser = await get_browser()
        page = await browser.new_page()

        if progress_callback:
            async def on_console(msg):
                if msg.type == "log":
                    text = msg.text
                    if text.startswith("__PROGRESS__:"):
                        try:
                            percent = int(text.split(":")[1])
                            await progress_callback(percent)
                        except:
                            pass
            page.on("console", on_console)

        try:
            await page.add_init_script("""
                (() => {
                    let reported = 0;
                    const observer = new PerformanceObserver((list) => {
                        const entries = performance.getEntriesByType("resource");
                        const total = entries.length || 20;
                        const loaded = entries.filter(e => e.responseEnd > 0).length;
                        let percent = Math.min(100, Math.round((loaded / total) * 100));
                        if (percent - reported >= 5) {
                            reported = percent;
                            console.log("__PROGRESS__:" + percent);
                        }
                    });
                    observer.observe({entryTypes: ["resource"]});
                })();
            """)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            content = await page.content()
            if progress_callback:
                await progress_callback(100)
            return content
        finally:
            await page.close()
