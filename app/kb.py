from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .textnorm import tokenize


@dataclass(frozen=True)
class KBEntry:
    id: str
    text: str
    metadata: dict

    @property
    def category(self) -> str:
        return str(self.metadata.get("category", ""))

    @property
    def topic(self) -> str:
        return str(self.metadata.get("topic", ""))

    @property
    def question(self) -> str:
        return str(self.metadata.get("question", ""))


def load_from_raw_folder(raw_dir: str | Path) -> list[KBEntry]:
    """
    Load KB from markdown files under raw/ and map into KBEntry.
    """
    from .kb_raw import load_raw_folder

    raw_entries = load_raw_folder(raw_dir)
    return [KBEntry(id=e.id, text=e.text, metadata=e.metadata) for e in raw_entries]


def _role_to_categories(role: str) -> set[str]:
    # Map decision-tree role => KB categories inside data.jsonl
    if role == "merchant":
        return {"Dành cho Nhà hàng"}
    if role == "driver":
        return {"Dành cho tài xế Taxi", "Dành cho tài xế Bike"}
    return {"Dành cho người dùng"}


def _score(query_tokens: set[str], entry: KBEntry) -> int:
    # Lightweight keyword overlap (accent-stripped tokens).
    # Consider title fields more important than body.
    q = set(tokenize(entry.question))
    t = set(tokenize(entry.topic))
    body = set(tokenize(entry.text))

    score = 0
    score += 8 * len(query_tokens & q)
    score += 3 * len(query_tokens & t)
    score += 1 * len(query_tokens & body)
    return score


def retrieve(entries: list[KBEntry], query: str, role: str, k: int = 5) -> list[KBEntry]:
    categories = _role_to_categories(role)
    filtered = [e for e in entries if e.category in categories]

    qt = set(tokenize(query))
    scored = [(e, _score(qt, e)) for e in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)

    top = [e for (e, s) in scored if s > 0][:k]
    if top:
        return top

    # If no overlaps, still return a small fallback slice from the role bucket.
    return filtered[: min(k, len(filtered))]

