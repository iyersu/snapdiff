"""The only network code in snapdiff: fetch a URL over HTTP(S).

Everything else in the package is offline and unit-testable without a network.
"""

from __future__ import annotations

import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 30
_USER_AGENT = "snapdiff/0.1 (+https://github.com/iyersu/snapdiff)"


class FetchError(Exception):
    """Raised when a URL cannot be fetched."""


def fetch(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Fetch ``url`` and return its body decoded as text.

    Raises :class:`FetchError` for any transport or protocol failure so callers
    have a single exception type to handle.
    """
    if not url.startswith(("http://", "https://")):
        raise FetchError(f"unsupported URL scheme: {url!r} (expected http/https)")

    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} fetching {url}: {exc.reason}") from exc
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise FetchError(f"could not fetch {url}: {reason}") from exc

    return raw.decode(charset, errors="replace")
