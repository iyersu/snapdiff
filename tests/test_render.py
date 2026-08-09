"""Tests for the opt-in headless-render fallback.

None of these launch a browser or touch the network. The Playwright import is
never triggered: we patch ``render._load_playwright`` to inject a fake or an
error, per the code-writer's guidance.
"""

import unittest
from unittest import mock

import importlib

from snapdiff.render import RenderError, looks_unrendered

# snapdiff/__init__.py exports a `render` *function*, which shadows the
# `snapdiff.render` submodule for attribute access. Grab the real module object
# so patch.object() targets module globals like `_load_playwright`.
render = importlib.import_module("snapdiff.render")


class LooksUnrenderedTests(unittest.TestCase):
    """Pure predicate: True when the HTML is empty or effectively text-less."""

    def test_empty_string_is_unrendered(self):
        self.assertTrue(looks_unrendered(""))

    def test_whitespace_only_is_unrendered(self):
        self.assertTrue(looks_unrendered("   \n\t  "))

    def test_script_only_shell_is_unrendered(self):
        shell = (
            "<html><head><script>var x=1</script></head>"
            "<body></body></html>"
        )
        # The only text lives in <script>, which html_to_text drops.
        self.assertTrue(looks_unrendered(shell))

    def test_real_content_past_threshold_is_rendered(self):
        html = (
            "<html><body><p>This is a real page with plenty of visible "
            "text well past the threshold.</p></body></html>"
        )
        self.assertFalse(looks_unrendered(html))

    def test_threshold_boundary(self):
        # Exactly MIN_VISIBLE_CHARS visible chars is NOT unrendered (uses <).
        text = "x" * render.MIN_VISIBLE_CHARS
        html = "<body>{}</body>".format(text)
        self.assertFalse(looks_unrendered(html))
        # One char short IS unrendered.
        short = "x" * (render.MIN_VISIBLE_CHARS - 1)
        self.assertTrue(looks_unrendered("<body>{}</body>".format(short)))


class RenderMissingDependencyTests(unittest.TestCase):
    """When Playwright cannot be imported, the render path must fail helpfully.

    Playwright is genuinely not installed in this environment, so we exercise the
    real ImportError->RenderError conversion rather than patching it. (Patching
    ``_load_playwright`` to raise a raw ImportError, as one might expect, does NOT
    yield RenderError: render() calls _load_playwright() outside try/except and
    relies on _load_playwright itself to do the conversion and supply the hints.)
    """

    def test_load_playwright_converts_import_error_to_render_error(self):
        with self.assertRaises(RenderError) as ctx:
            render._load_playwright()
        msg = str(ctx.exception)
        self.assertIn("pip install", msg)
        self.assertIn("playwright install chromium", msg)

    def test_render_propagates_render_error_when_dependency_missing(self):
        with self.assertRaises(RenderError) as ctx:
            render.render("https://x.test")
        msg = str(ctx.exception)
        self.assertIn("pip install", msg)
        self.assertIn("playwright install chromium", msg)


# ---------------------------------------------------------------------------
# Fake sync_playwright chain for the success path. No browser, no network.
# ---------------------------------------------------------------------------


class _FakePage:
    def __init__(self, html):
        self._html = html
        self.goto_calls = []

    def goto(self, url, timeout=None, **kwargs):
        self.goto_calls.append((url, timeout, kwargs))

    def content(self):
        return self._html


class _FakeBrowser:
    def __init__(self, page):
        self._page = page
        self.closed = False

    def new_page(self):
        return self._page

    def close(self):
        self.closed = True


class _FakeChromium:
    def __init__(self, browser):
        self._browser = browser
        self.launch_kwargs = None

    def launch(self, **kwargs):
        self.launch_kwargs = kwargs
        return self._browser


class _FakePlaywright:
    def __init__(self, chromium):
        self.chromium = chromium


class _FakeSyncContext:
    """What sync_playwright() returns: a context manager yielding playwright."""

    def __init__(self, playwright):
        self._playwright = playwright
        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        return self._playwright

    def __exit__(self, *exc):
        self.exited = True
        return False


class RenderSuccessPathTests(unittest.TestCase):
    """Drive render() through a fully faked Playwright chain."""

    def test_render_returns_page_content_and_closes_browser(self):
        expected_html = "<html><body><p>Rendered content</p></body></html>"
        page = _FakePage(expected_html)
        browser = _FakeBrowser(page)
        chromium = _FakeChromium(browser)
        playwright = _FakePlaywright(chromium)
        ctx = _FakeSyncContext(playwright)

        # sync_playwright is a zero-arg callable returning the context manager.
        fake_sync_playwright = mock.Mock(return_value=ctx)

        with mock.patch.object(
            render, "_load_playwright", return_value=fake_sync_playwright
        ):
            result = render.render("https://x.test")

        self.assertEqual(result, expected_html)
        self.assertTrue(browser.closed, "browser.close() must be called")
        self.assertTrue(ctx.exited, "sync_playwright context must be exited")
        self.assertEqual(chromium.launch_kwargs, {"headless": True})
        self.assertEqual(len(page.goto_calls), 1)
        self.assertEqual(page.goto_calls[0][0], "https://x.test")


if __name__ == "__main__":
    unittest.main()
