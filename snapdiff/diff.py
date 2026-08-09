"""Compute and describe the delta between two snapshots. Pure functions, no I/O."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field


@dataclass
class Delta:
    """The difference between an old snapshot and a new one."""

    is_first_run: bool
    changed: bool
    added_lines: int
    removed_lines: int
    unified_diff: str = ""
    added_samples: list[str] = field(default_factory=list)
    removed_samples: list[str] = field(default_factory=list)


def diff_snapshots(old: str | None, new: str, *, context: int = 3) -> Delta:
    """Compare ``old`` (may be ``None`` on first run) against ``new``."""
    if old is None:
        return Delta(is_first_run=True, changed=True, added_lines=0, removed_lines=0)

    old_lines = old.splitlines()
    new_lines = new.splitlines()

    added_samples: list[str] = []
    removed_samples: list[str] = []
    added = removed = 0
    for line in difflib.ndiff(old_lines, new_lines):
        if line.startswith("+ "):
            added += 1
            if len(added_samples) < 5:
                added_samples.append(line[2:])
        elif line.startswith("- "):
            removed += 1
            if len(removed_samples) < 5:
                removed_samples.append(line[2:])

    unified = "\n".join(
        difflib.unified_diff(
            old_lines, new_lines, fromfile="previous", tofile="current", lineterm="", n=context
        )
    )

    return Delta(
        is_first_run=False,
        changed=added > 0 or removed > 0,
        added_lines=added,
        removed_lines=removed,
        unified_diff=unified,
        added_samples=added_samples,
        removed_samples=removed_samples,
    )


def describe_delta(url: str, delta: Delta) -> str:
    """Render a short, human-readable summary of a :class:`Delta`."""
    if delta.is_first_run:
        return f"First snapshot of {url}. Baseline saved; nothing to compare yet."

    if not delta.changed:
        return f"No change at {url}."

    parts = [f"Change detected at {url}:"]
    if delta.added_lines:
        parts.append(f"  +{delta.added_lines} line(s) added")
        for sample in delta.added_samples:
            parts.append(f"    + {sample}")
    if delta.removed_lines:
        parts.append(f"  -{delta.removed_lines} line(s) removed")
        for sample in delta.removed_samples:
            parts.append(f"    - {sample}")
    return "\n".join(parts)
