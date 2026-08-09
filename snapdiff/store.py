"""Snapshot storage on the local filesystem.

One snapshot per URL, keyed by a hash of the URL. No network, no database.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

DEFAULT_DIR = ".snapshots"


def _key(url: str) -> str:
    """Stable, filesystem-safe key for a URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


class SnapshotStore:
    """Reads and writes the last-seen content for each URL under a directory."""

    def __init__(self, directory: str | Path = DEFAULT_DIR) -> None:
        self.directory = Path(directory)

    def _paths(self, url: str) -> tuple[Path, Path]:
        key = _key(url)
        return (
            self.directory / f"{key}.snapshot",
            self.directory / f"{key}.meta.json",
        )

    def load(self, url: str) -> Optional[str]:
        """Return the last saved content for ``url``, or ``None`` if unseen."""
        snapshot_path, _ = self._paths(url)
        if not snapshot_path.exists():
            return None
        return snapshot_path.read_text(encoding="utf-8")

    def save(self, url: str, content: str) -> None:
        """Save ``content`` as the new baseline for ``url``."""
        self.directory.mkdir(parents=True, exist_ok=True)
        snapshot_path, meta_path = self._paths(url)
        snapshot_path.write_text(content, encoding="utf-8")
        meta_path.write_text(
            json.dumps({"url": url, "bytes": len(content.encode("utf-8"))}, indent=2),
            encoding="utf-8",
        )
