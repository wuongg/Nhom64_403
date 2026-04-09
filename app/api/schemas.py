from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RoleName = Literal["user", "driver", "merchant"]
RoleMode = Literal["auto", "llm", "rule"]
MessageActor = Literal["user", "assistant"]
FeedbackVerdict = Literal["helpful", "not_helpful"]
FeedbackReason = Literal["wrong_intent", "wrong_answer", "missing_info", "handoff_needed", "other"]
MessageMode = Literal["answer", "preview"]


class HealthResponse(BaseModel):
    status: str
    kb_loaded: bool
    openai_configured: bool


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str


class MessageRequest(BaseModel):
    message: str = Field(min_length=1)
    role_override: RoleName | None = None
    role_mode: RoleMode = "auto"
    k: int | None = Field(default=None, ge=1)
    model: str | None = None


class RoleDecisionResponse(BaseModel):
    role: RoleName
    safety: bool
    driver_type: str | None = None
    reason: str


class KBHitResponse(BaseModel):
    id: str
    topic: str
    question: str
    category: str


class MetricsResponse(BaseModel):
    model: str
    latency_ms: float
    usage: dict
    cost_usd_estimate: float | None = None


class RetryAttemptResponse(BaseModel):
    attempt: int
    model_used: str
    error: str | None = None
    delay_before: float = 0.0


class RetryInfoResponse(BaseModel):
    attempts: list[RetryAttemptResponse]
    used_fallback_model: bool


class MessageResponse(BaseModel):
    session_id: str
    user_message_id: str
    assistant_message_id: str | None = None
    mode: MessageMode
    answer: str | None = None
    role_decision: RoleDecisionResponse
    kb_hits: list[KBHitResponse]
    handoff_recommended: bool
    handoff_reason: str
    metrics: MetricsResponse | None = None
    retry_info: RetryInfoResponse | None = None


class FeedbackRequest(BaseModel):
    message_id: str
    verdict: FeedbackVerdict
    reason: FeedbackReason
    note: str | None = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    session_id: str
    stored: bool


class MessageItemResponse(BaseModel):
    id: str
    actor: MessageActor
    content: str
    role: RoleName | None = None
    safety: bool
    handoff_recommended: bool
    handoff_reason: str | None = None
    model: str | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd_estimate: float | None = None
    kb_hits: list[KBHitResponse] = Field(default_factory=list)
    created_at: str


class SessionDetailResponse(BaseModel):
    session_id: str
    status: str
    created_at: str
    updated_at: str
    messages: list[MessageItemResponse]
