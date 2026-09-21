"""
Deduplication and content hashing store for SyncLM Studio.
Uses SHA-256 hashing to avoid redundant fetches and Google Docs API batch updates.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def get_hashes_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "hashes.json"


def compute_hash(content: str) -> str:
    """Compute normalized SHA-256 hash of text content."""
    # Normalize line endings and trailing whitespace before hashing
    normalized = "\n".join(line.rstrip() for line in content.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class HashStore:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or get_hashes_path()
        self._hashes: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._hashes = json.load(f)
            except Exception:
                self._hashes = {}
        else:
            self._hashes = {}

    def save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._hashes, f, indent=2, sort_keys=True)

    def is_changed(self, source_id: str, new_content: str) -> Tuple[bool, str, Optional[str]]:
        """
        Determines if the content for a source_id has changed.
        Returns (is_changed, current_hash, previous_hash).
        """
        new_hash = compute_hash(new_content)
        entry = self._hashes.get(source_id)
        if not entry:
            return True, new_hash, None
        
        prev_hash = entry.get("sha256")
        return new_hash != prev_hash, new_hash, prev_hash

    def update(self, source_id: str, content: str, url: str) -> str:
        """Update hash store with latest content hash."""
        new_hash = compute_hash(content)
        now = datetime.now(timezone.utc).isoformat()
        self._hashes[source_id] = {
            "sha256": new_hash,
            "url": url,
            "updated_at": now,
            "char_count": len(content),
            "word_count": len(content.split())
        }
        self.save()
        return new_hash

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tracked_sources": len(self._hashes),
            "total_words_cached": sum(e.get("word_count", 0) for e in self._hashes.values()),
            "latest_update": max((e.get("updated_at") for e in self._hashes.values()), default=None)
        }
