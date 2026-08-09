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
    parser.add_argument("--version", action="version", version=f"snapdiff {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = SnapshotStore(args.dir)

    try:
        current = fetch(args.url)
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    previous = store.load(args.url)
    delta = diff_snapshots(previous, current)

    print(describe_delta(args.url, delta))
    if args.show_diff and delta.unified_diff:
        print()
        print(delta.unified_diff)

    if not args.no_save:
        store.save(args.url, current)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
