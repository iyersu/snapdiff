"""Command-line entry point: orchestrate fetch -> diff -> describe -> save."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .diff import describe_delta, diff_snapshots
from .fetch import FetchError, fetch
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
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FETCH_ERROR

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
