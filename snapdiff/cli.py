"""Command-line entry point: orchestrate fetch -> diff -> describe -> save."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .diff import describe_delta, diff_snapshots
from .fetch import FetchError, fetch
from .htmltext import html_to_text
from .render import RenderError, looks_unrendered, render
from .select import SelectError, select_text
from .store import DEFAULT_DIR, SnapshotStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snapdiff",
        description="Fetch a URL, diff it against the last snapshot, and describe the delta.",
    )
    parser.add_argument("url", help="the http(s) URL to snapshot")
    parser.add_argument(
        "--dir",
        default=DEFAULT_DIR,
        help=f"directory to store snapshots in (default: {DEFAULT_DIR})",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help="print the full unified diff in addition to the summary",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="reduce fetched HTML to visible text before diffing, so markup-only "
        "churn stops producing false positives",
    )
    parser.add_argument(
        "--select",
        default=None,
        metavar="SELECTOR",
        help="reduce fetched/rendered HTML to the visible text of matching "
        "elements before diffing, e.g. watch just a price with 'span.price'; "
        "supports a small CSS subset (tag, .class, #id, and compounds like "
        "span.price). Exits non-zero if the selector is unsupported or matches "
        "no elements",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="if the plain fetch looks empty/unrendered (e.g. a JS-heavy page), "
        "re-fetch it with a headless browser; needs the optional Playwright extra "
        "(pip install -r requirements-render.txt && playwright install chromium)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="do not update the saved baseline (dry run)",
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="exit with code 2 when a change is detected (for cron/CI monitoring); "
        "the first-run baseline is not treated as a change",
    )
    parser.add_argument("--version", action="version", version=f"snapdiff {__version__}")
    return parser


# Exit codes
EXIT_OK = 0
EXIT_FETCH_ERROR = 1
EXIT_CHANGED = 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.dir)

    try:
        current = fetch(args.url)
        if args.render and looks_unrendered(current):
            current = render(args.url)
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FETCH_ERROR

    # EXIT_FETCH_ERROR (1) covers fetch and selection errors alike.
    # Use `is not None` so an empty --select '' errors loudly instead of being
    # treated as unset (consistent with the feature's fail-loudly stance).
    if args.select is not None:
        try:
            current = select_text(current, args.select)
        except SelectError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_FETCH_ERROR

    if args.text:
        current = html_to_text(current)

    previous = store.load(args.url)
    delta = diff_snapshots(previous, current)

    print(describe_delta(args.url, delta))
    if args.show_diff and delta.unified_diff:
        print()
        print(delta.unified_diff)

    if not args.no_save:
        store.save(args.url, current)

    # A first-run baseline is not a change worth failing on.
    if args.fail_on_change and delta.changed and not delta.is_first_run:
        return EXIT_CHANGED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
