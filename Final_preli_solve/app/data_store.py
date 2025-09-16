
from __future__ import annotations
import json
import threading
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class InMemoryStore:
    """
    Simple, thread-safe in-memory store with optional JSON persistence.
    """
    def __init__(self, persist_path: Optional[str] = None):
        self._lock = threading.RLock()
        self.voters: Dict[str, dict] = {}
        self.candidates: Dict[str, dict] = {}
        self.votes: List[dict] = []
        self.encrypted_ballots: List[dict] = []
        self.metrics: Dict[str, Any] = {"start_time": time.time(), "requests": 0}
        self.persist_path = Path(persist_path) if persist_path else None
        if self.persist_path and self.persist_path.exists():
            self._load()

    def _load(self):
        try:
            with self._lock, self.persist_path.open("r", encoding="utf-8") as f:
                blob = json.load(f)
                self.voters = blob.get("voters", {})
                self.candidates = blob.get("candidates", {})
                self.votes = blob.get("votes", [])
                self.encrypted_ballots = blob.get("encrypted_ballots", [])
        except Exception:
            # ignore load errors (start clean)
            pass

    def save(self):
        if not self.persist_path:
            return
        blob = {
            "voters": self.voters,
            "candidates": self.candidates,
            "votes": self.votes,
            "encrypted_ballots": self.encrypted_ballots,
        }
        with self._lock, self.persist_path.open("w", encoding="utf-8") as f:
            json.dump(blob, f, indent=2)

    def reset(self):
        with self._lock:
            self.voters.clear()
            self.candidates.clear()
            self.votes.clear()
            self.encrypted_ballots.clear()

store = InMemoryStore(persist_path="/data/state.json")
