"""Reduce HTML to the visible text of elements matching a tiny CSS subset.

Pure functions, no I/O. Supports one compound selector built from a tag name,
``.class`` tokens, and a ``#id`` token (e.g. ``span.price``). Anything richer —
combinators, attribute selectors, pseudo-classes, ``,`` lists, ``*`` — is
rejected with :class:`SelectError`.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional

from .htmltext import html_to_text

# Void elements never have a closing tag, so they must not push the depth
# counter used to find an element's own end tag.
_VOID_TAGS = {
    "br", "img", "hr", "input", "meta", "link",
    "area", "base", "col", "embed", "source", "track", "wbr",
}

# A leading tag name, then zero-or-more ``.class`` / ``#id`` tokens.
_SELECTOR_RE = re.compile(r"^([A-Za-z][\w-]*)?((?:[.#][\w-]+)*)$")
_TOKEN_RE = re.compile(r"([.#])([\w-]+)")


class SelectError(Exception):
    """Raised for an unsupported selector or one that matched no elements.

    This is a usage/content problem, deliberately *not* a ``FetchError``, so the
    CLI handles it outside the fetch/render try block.
    """


def _parse_selector(selector: str) -> tuple[Optional[str], frozenset[str], Optional[str]]:
    """Parse one compound selector into ``(tag, classes, id)``.

    Raises :class:`SelectError` on anything outside the supported subset.
    """
    match = _SELECTOR_RE.match(selector.strip()) if selector else None
    if match is None:
        raise SelectError(
            f"unsupported selector: {selector}; "
            "supported: tag, .class, #id and compounds like span.price"
        )

    # HTMLParser lowercases tag names, so lowercase the selector's tag to match.
    # Class and id values stay case-sensitive (HTML treats them so).
    tag = match.group(1).lower() if match.group(1) else None
    classes = set()
    element_id: Optional[str] = None
    for kind, name in _TOKEN_RE.findall(match.group(2)):
        if kind == ".":
            classes.add(name)
        elif element_id is not None:
            raise SelectError(
                f"unsupported selector: {selector}; "
                "supported: tag, .class, #id and compounds like span.price"
            )
        else:
            element_id = name

    if tag is None and not classes and element_id is None:
        raise SelectError(
            f"unsupported selector: {selector}; "
            "supported: tag, .class, #id and compounds like span.price"
        )
    return tag, frozenset(classes), element_id


class _Selector(HTMLParser):
    """Capture the inner HTML of each outermost element matching a selector."""

    def __init__(self, tag: Optional[str], classes: frozenset[str], element_id: Optional[str]) -> None:
        super().__init__(convert_charrefs=False)
        self._tag = tag
        self._classes = classes
        self._id = element_id
        self.fragments: list[str] = []
        self._parts: list[str] = []
        self._depth = 0  # open-tag depth inside the matched element

    def _matches(self, tag: str, attrs: list) -> bool:
        if self._tag is not None and tag != self._tag:
            return False
        attr = dict(attrs)
        element_classes = set((attr.get("class") or "").split())
        if not self._classes <= element_classes:
            return False
        if self._id is not None and attr.get("id") != self._id:
            return False
        return True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if self._depth:
            # Already capturing: record the raw start tag as inner HTML.
            self._parts.append(self.get_starttag_text() or "")
            if tag not in _VOID_TAGS:
                self._depth += 1
        elif self._matches(tag, attrs) and tag not in _VOID_TAGS:
            # Begin a fresh capture; depth 1 is the element's own open tag.
            self._depth = 1

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        if self._depth:
            self._parts.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if self._depth == 0:
            self.fragments.append("".join(self._parts))
            self._parts = []
        else:
            self._parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        # convert_charrefs=False, so entities arrive here; keep the raw markup
        # intact so html_to_text can decode it from the captured fragment.
        if self._depth:
            self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._depth:
            self._parts.append(f"&#{name};")


def select_text(html: str, selector: str) -> str:
    """Return the visible text of elements in ``html`` matching ``selector``.

    Parses ``selector`` once, captures each matching element's inner HTML, and
    reduces every fragment with :func:`html_to_text`. Raises :class:`SelectError`
    if the selector is unsupported or matches nothing.
    """
    tag, classes, element_id = _parse_selector(selector)
    parser = _Selector(tag, classes, element_id)
    parser.feed(html)
    parser.close()

    if not parser.fragments:
        raise SelectError(f"selector {selector!r} matched no elements")
    return "\n".join(html_to_text(fragment) for fragment in parser.fragments)
