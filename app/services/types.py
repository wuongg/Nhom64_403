from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..kb import KBEntry, ScoredKBEntry
from ..llm import ChatResult
from ..prompting import PromptBundle
from ..role_tree import RoleDecision
from ..llm_retry import RetryAttempt

# Re-export for convenience
__all__ = [
    "KnowledgeBaseHit",
    "KnowledgeBaseSearchResult",
    "HandoffDecision",
    "ChatPrepared",
    "ChatTurnResult",
]


@dataclass(frozen=True, slots=True)
class KnowledgeBaseHit:
    id: str
    category: str
    topic: str
    question: str

    @classmethod
    def from_entry(cls, entry: KBEntry) -> "KnowledgeBaseHit":
        return cls(
            id=entry.id,
            category=entry.category,
            topic=entry.topic,
            question=entry.question,
        )


@dataclass(frozen=True, slots=True)
class KnowledgeBaseSearchResult:
    entry: KBEntry
    score: int

    @classmethod
    def from_scored_entry(cls, scored: ScoredKBEntry) -> "KnowledgeBaseSearchResult":
        return cls(entry=scored.entry, score=scored.score)

    @property
    def id(self) -> str:
        return self.entry.id

    @property
    def category(self) -> str:
        return self.entry.category

    @property
    def topic(self) -> str:
        return self.entry.topic

    @property
    def question(self) -> str:
        return self.entry.question

    def to_hit(self) -> KnowledgeBaseHit:
        return KnowledgeBaseHit.from_entry(self.entry)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "topic": self.topic,
            "question": self.question,
        }


@dataclass(frozen=True, slots=True)
class HandoffDecision:
    recommended: bool
    reason: str
    trigger: str


@dataclass(frozen=True, slots=True)
class ChatPrepared:
    """Holds all pre-LLM state: role decision, KB results, handoff, and prompt.
    Produced by ChatService.prepare(); consumed by the streaming route."""

    query: str
    role_decision: RoleDecision
    kb_results: tuple[KnowledgeBaseSearchResult, ...]
    kb_hits: tuple[KnowledgeBaseHit, ...]
    handoff: HandoffDecision
    prompt: PromptBundle
    active_model: str
    mode: str           # "answer" | "preview"
    preview_only: bool
    note: str | None
    debug: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ChatTurnResult:
    query: str
    role_decision: RoleDecision
    kb_results: tuple[KnowledgeBaseSearchResult, ...]
    kb_hits: tuple[KnowledgeBaseHit, ...]
    handoff: HandoffDecision
    mode: str
    preview_only: bool
    prompt: PromptBundle
    answer: ChatResult | None
    model: str
    retry_attempts: tuple[RetryAttempt, ...] = field(default_factory=tuple)
    used_fallback_model: bool = False
    note: str | None = None
    debug: dict[str, Any] = field(default_factory=dict)
