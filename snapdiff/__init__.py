"""snapdiff — fetch a URL, diff it against the last snapshot, describe the delta."""

__version__ = "0.1.0"

from .diff import Delta, describe_delta, diff_snapshots
from .htmltext import html_to_text
from .store import SnapshotStore

__all__ = [
    "Delta",
    "describe_delta",
    "diff_snapshots",
    "html_to_text",
    "SnapshotStore",
    "__version__",
]
