from functools import lru_cache
from .renderer import render_page

@lru_cache(maxsize=64)
def _key_safe(url: str) -> str:
    return url.strip().lower()

_cache = {}

async def get_or_render_cached(url: str) -> str:
    key = _key_safe(url)
    if key in _cache:
        return _cache[key]
    html = await render_page(url)
    _cache[key] = html
    return html
