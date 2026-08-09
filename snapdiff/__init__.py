"""snapdiff — fetch a URL, diff it against the last snapshot, describe the delta."""

__version__ = "0.1.0"

from .diff import Delta, describe_delta, diff_snapshots
from .store import SnapshotStore

__all__ = ["Delta", "describe_delta", "diff_snapshots", "SnapshotStore", "__version__"]
