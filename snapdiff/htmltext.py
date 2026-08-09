"""Reduce HTML to visible text. Pure function, no I/O."""

from __future__ import annotations

from html.parser import HTMLParser

# Tags whose text content should be dropped entirely.
_SKIP_TAGS = {"script", "style"}

# Tags that should force a line break in the extracted text.
_BLOCK_TAGS = {
    "p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "td", "th", "ul", "ol", "section", "article", "header", "footer", "table",
}


class _TextExtractor(HTMLParser):
    """Collect visible text, skipping script/style and breaking on block tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def html_to_text(html: str) -> str:
    """Extract visible text from ``html``.

    Skips ``<script>``/``<style>`` content, treats block-level tags as line
    breaks, and normalizes whitespace. Stable for real usage: each snapshot is
    reduced exactly once from its own raw HTML, and re-reducing plain text is a
    no-op (unless that text itself contains entity-encoded markup).
    """
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()

    lines = []
    for line in parser.text().splitlines():
        line = " ".join(line.split())
        if line:
            lines.append(line)
    return "\n".join(lines)
