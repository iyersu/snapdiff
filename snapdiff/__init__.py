"""snapdiff — fetch a URL, diff it against the last snapshot, describe the delta."""

__version__ = "0.1.0"

from .diff import Delta, describe_delta, diff_snapshots
from .htmltext import html_to_text
# NB: do not export the ``render`` function here — it would shadow the
# ``snapdiff.render`` submodule. cli.py imports it directly from .render.
from .render import RenderError, looks_unrendered
from .select import SelectError, select_text
from .store import SnapshotStore

__all__ = [
    "Delta",
    "describe_delta",
    "diff_snapshots",
    "html_to_text",
    "looks_unrendered",
    "RenderError",
    "SelectError",
    "select_text",
    "SnapshotStore",
    "__version__",
]
