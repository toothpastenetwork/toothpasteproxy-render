from diskcache import Cache
from .renderer import render_page
import asyncio

cache = Cache("./.render_cache")

def get_key(url: str) -> str:
    return url.strip().lower()

async def get_or_render_cached(url: str) -> str:
    key = get_key(url)
    if key in cache:
        return cache[key]
    html = await render_page(url)
    cache.set(key, html, expire=86400)  # 1 day TTL
    return html

# Optional: Background refresh
def refresh_async(url: str):
    key = get_key(url)
    async def _refresh():
        html = await render_page(url)
        cache.set(key, html, expire=86400)
    asyncio.create_task(_refresh())
