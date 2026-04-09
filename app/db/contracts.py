from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ChatSessionRecord:
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    summary: str | None = None


@dataclass(frozen=True, slots=True)
class ChatMessageRecord:
    id: str
    session_id: str
    actor: str
    content: str
    role: str | None
    safety: bool
    handoff_recommended: bool
    handoff_reason: str | None
    model: str | None
    latency_ms: float | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    cost_usd_estimate: float | None
    kb_hits_json: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class MessageFeedbackRecord:
    id: str
    session_id: str
    message_id: str
    verdict: str
    reason: str
    note: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SessionDetails:
    session: ChatSessionRecord
    messages: tuple[ChatMessageRecord, ...] = field(default_factory=tuple)
    feedback: tuple[MessageFeedbackRecord, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MessageWrite:
    session_id: str
    actor: str
    content: str
    role: str | None = None
    safety: bool = False
    handoff_recommended: bool = False
    handoff_reason: str | None = None
    model: str | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd_estimate: float | None = None
    kb_hits: Sequence[Mapping[str, Any]] | None = None


@dataclass(frozen=True, slots=True)
class FeedbackWrite:
    session_id: str
    message_id: str
    verdict: str
    reason: str
    note: str | None = None
