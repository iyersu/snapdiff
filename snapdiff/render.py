"""Optional headless-browser render fallback for JS-rendered pages.

This is the only browser code in snapdiff, and it is opt-in. Playwright is a
third-party extra imported lazily inside :func:`_load_playwright` so the rest of
the package (and the default fetch path) stays stdlib-only and importable even
when Playwright is not installed.
"""

from __future__ import annotations

from .fetch import FetchError
from .htmltext import html_to_text

MIN_VISIBLE_CHARS = 32
DEFAULT_RENDER_TIMEOUT = 30


class RenderError(FetchError):
    """Raised when a page cannot be rendered.

    Subclasses :class:`FetchError` so the CLI's existing handler catches it.
    """


def looks_unrendered(html: str, *, min_visible_chars: int = MIN_VISIBLE_CHARS) -> bool:
    """Return True if ``html`` looks empty or effectively text-less.

    Pure function, no I/O. Used to decide whether the render fallback is worth
    triggering after a plain fetch.
    """
    if not html.strip():
        return True
    return len(html_to_text(html)) < min_visible_chars


def _load_playwright():
    """Import Playwright lazily and return ``sync_playwright``.

    A tiny indirection so the import stays lazy and tests can patch this one
    function. Raises :class:`RenderError` with install hints when Playwright is
    not available.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RenderError(
            "--render needs Playwright. Install it with: "
            "pip install -r requirements-render.txt && playwright install chromium"
        ) from exc
    return sync_playwright


def render(url: str, *, timeout: float = DEFAULT_RENDER_TIMEOUT) -> str:
    """Render ``url`` in headless Chromium and return the resulting HTML.

    Raises :class:`RenderError` on any failure so the CLI has a single exception
    type to handle.
    """
    sync_playwright = _load_playwright()
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:
            raise RenderError(
                "could not launch Chromium. Install the browser with: "
                "playwright install chromium"
            ) from exc
        try:
            page = browser.new_page()
            # Wait for the network to settle so JS-rendered content is painted,
            # not just the initial shell — the whole reason to use a browser.
            page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            return page.content()
        except Exception as exc:
            raise RenderError(f"could not render {url}: {exc}") from exc
        finally:
            browser.close()
