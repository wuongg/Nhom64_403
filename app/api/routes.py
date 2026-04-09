from __future__ import annotations

import json
from datetime import datetime

from pydantic import ValidationError

from ..db import FeedbackWrite, MessageWrite
from ..db.contracts import ChatMessageRecord
from ..llm import ChatResult, chat_openai_stream_async
from .framework import APIRouter, HTTPException, Request, StreamingResponse
from .schemas import (
    CreateSessionResponse,
    FeedbackRequest,
    FeedbackResponse,
    KBHitResponse,
    MessageItemResponse,
    MessageRequest,
    MessageResponse,
    MetricsResponse,
    RoleDecisionResponse,
    SessionDetailResponse,
)


router = APIRouter(prefix="/api/v1")


def _container(request: Request):
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(503, "Application container is not ready")
    return container


def _iso(value: datetime) -> str:
    return value.isoformat()


def _kb_hits_from_json(raw: str | None) -> list[dict]:
    if not raw:
        return []
    return json.loads(raw)


def _role_decision_payload(decision) -> RoleDecisionResponse:
    return RoleDecisionResponse(
        role=decision.role,
        safety=decision.safety,
        driver_type=decision.driver_type,
        reason=decision.reason,
    )


def _kb_hits_payload(hits) -> list[KBHitResponse]:
    return [
        KBHitResponse(
            id=hit.id,
            topic=hit.topic,
            question=hit.question,
            category=hit.category,
        )
        for hit in hits
    ]


def _metrics_payload(result) -> MetricsResponse:
    return MetricsResponse(**result.to_dict())


def _message_item_payload(message: ChatMessageRecord) -> MessageItemResponse:
    return MessageItemResponse(
        id=message.id,
        actor=message.actor,
        content=message.content,
        role=message.role,
        safety=message.safety,
        handoff_recommended=message.handoff_recommended,
        handoff_reason=message.handoff_reason,
        model=message.model,
        latency_ms=message.latency_ms,
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        total_tokens=message.total_tokens,
        cost_usd_estimate=message.cost_usd_estimate,
        kb_hits=[KBHitResponse(**hit) for hit in _kb_hits_from_json(message.kb_hits_json)],
        created_at=_iso(message.created_at),
    )


@router.post("/sessions")
def create_session(request: Request) -> CreateSessionResponse:
    container = _container(request)
    record = container.store.create_session()
    return CreateSessionResponse(
        session_id=record.id,
        created_at=_iso(record.created_at),
    )


@router.get("/sessions/{session_id}")
def get_session(request: Request, session_id: str) -> SessionDetailResponse:
    container = _container(request)
    detail = container.store.get_session_details(session_id)
    if detail is None:
        raise HTTPException(404, "Session not found")

    return SessionDetailResponse(
        session_id=detail.session.id,
        status=detail.session.status,
        created_at=_iso(detail.session.created_at),
        updated_at=_iso(detail.session.updated_at),
        messages=[_message_item_payload(message) for message in detail.messages],
    )


@router.post("/sessions/{session_id}/messages")
async def post_message(request: Request, session_id: str) -> MessageResponse:
    container = _container(request)
    session_details = container.store.get_session_details(session_id)
    if session_details is None:
        raise HTTPException(404, "Session not found")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Invalid JSON body: {exc}") from exc

    try:
        body = MessageRequest(**(payload or {}))
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc

    turn = container.chat_service.process(
        body.message,
        role_mode=body.role_mode,
        role_override=body.role_override,
        k=body.k,
        model=body.model,
        session_details=session_details,
    )

    if turn.new_summary is not None:
        container.store.update_session_summary(session_id, turn.new_summary)

    user_message = container.store.add_message(
        MessageWrite(
            session_id=session_id,
            actor="user",
            content=body.message,
            role=turn.role_decision.role,
            safety=turn.role_decision.safety,
            handoff_recommended=turn.handoff.recommended,
            handoff_reason=turn.handoff.reason,
            model=turn.model,
            kb_hits=[hit.to_public_dict() for hit in turn.kb_results],
        )
    )

    assistant_message = None
    if turn.answer is not None:
        assistant_message = container.store.add_message(
            MessageWrite(
                session_id=session_id,
                actor="assistant",
                content=turn.answer.text,
                role=turn.role_decision.role,
                safety=turn.role_decision.safety,
                handoff_recommended=turn.handoff.recommended,
                handoff_reason=turn.handoff.reason,
                model=turn.answer.model,
                latency_ms=turn.answer.latency_ms,
                input_tokens=turn.answer.usage.input_tokens,
                output_tokens=turn.answer.usage.output_tokens,
                total_tokens=turn.answer.usage.total_tokens,
                cost_usd_estimate=turn.answer.cost_usd_estimate,
                kb_hits=[hit.to_public_dict() for hit in turn.kb_results],
            )
        )

    return MessageResponse(
        session_id=session_id,
        user_message_id=user_message.id,
        assistant_message_id=None if assistant_message is None else assistant_message.id,
        mode=turn.mode,
        answer=None if turn.answer is None else turn.answer.text,
        role_decision=_role_decision_payload(turn.role_decision),
        kb_hits=_kb_hits_payload(turn.kb_hits),
        handoff_recommended=turn.handoff.recommended,
        handoff_reason=turn.handoff.reason,
        metrics=None if turn.answer is None else _metrics_payload(turn.answer),
    )


@router.post("/sessions/{session_id}/messages/stream")
async def post_message_stream(request: Request, session_id: str) -> StreamingResponse:
    """Server-Sent Events endpoint for streaming LLM responses.

    SSE event types:
    - ``meta``  — sent immediately; contains KB hits, role decision, handoff, mode.
    - ``chunk`` — one text fragment from the LLM stream.
    - ``done``  — final event; contains assistant_message_id and full metrics.
    - ``error`` — if the LLM call fails mid-stream.
    """
    container = _container(request)
    session_details = container.store.get_session_details(session_id)
    if session_details is None:
        raise HTTPException(404, "Session not found")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Invalid JSON body: {exc}") from exc

    try:
        body = MessageRequest(**(payload or {}))
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc

    # ── Pre-LLM work (sync, fast) ────────────────────────────────────────────
    prepared = container.chat_service.prepare(
        body.message,
        role_mode=body.role_mode,
        role_override=body.role_override,
        k=body.k,
        model=body.model,
        session_details=session_details,
    )

    if prepared.new_summary is not None:
        container.store.update_session_summary(session_id, prepared.new_summary)

    user_message = container.store.add_message(
        MessageWrite(
            session_id=session_id,
            actor="user",
            content=body.message,
            role=prepared.role_decision.role,
            safety=prepared.role_decision.safety,
            handoff_recommended=prepared.handoff.recommended,
            handoff_reason=prepared.handoff.reason,
            model=prepared.active_model,
            kb_hits=[hit.to_public_dict() for hit in prepared.kb_results],
        )
    )

    # ── SSE generator ────────────────────────────────────────────────────────
    async def event_stream():
        def _sse(obj: dict) -> str:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

        # 1. meta — lets the frontend render KB hits and role info immediately
        yield _sse({
            "type": "meta",
            "session_id": session_id,
            "user_message_id": user_message.id,
            "mode": prepared.mode,
            "role_decision": {
                "role": prepared.role_decision.role,
                "safety": prepared.role_decision.safety,
                "driver_type": prepared.role_decision.driver_type,
                "reason": prepared.role_decision.reason,
            },
            "kb_hits": [
                {
                    "id": h.id,
                    "topic": h.topic,
                    "question": h.question,
                    "category": h.category,
                }
                for h in prepared.kb_hits
            ],
            "handoff_recommended": prepared.handoff.recommended,
            "handoff_reason": prepared.handoff.reason,
        })

        if prepared.preview_only:
            yield _sse({"type": "done", "assistant_message_id": None, "metrics": None})
            return

        # 2. LLM stream — yield one chunk per token batch
        final_result: ChatResult | None = None
        try:
            async for item in chat_openai_stream_async(
                prepared.prompt.system,
                prepared.prompt.user,
                history=prepared.prompt.history,
                model=prepared.active_model,
            ):
                if isinstance(item, str):
                    yield _sse({"type": "chunk", "text": item})
                else:
                    final_result = item
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})
            return

        # 3. Persist assistant message, send done
        assistant_message = None
        if final_result is not None:
            assistant_message = container.store.add_message(
                MessageWrite(
                    session_id=session_id,
                    actor="assistant",
                    content=final_result.text,
                    role=prepared.role_decision.role,
                    safety=prepared.role_decision.safety,
                    handoff_recommended=prepared.handoff.recommended,
                    handoff_reason=prepared.handoff.reason,
                    model=final_result.model,
                    latency_ms=final_result.latency_ms,
                    input_tokens=final_result.usage.input_tokens,
                    output_tokens=final_result.usage.output_tokens,
                    total_tokens=final_result.usage.total_tokens,
                    cost_usd_estimate=final_result.cost_usd_estimate,
                    kb_hits=[hit.to_public_dict() for hit in prepared.kb_results],
                )
            )

        yield _sse({
            "type": "done",
            "assistant_message_id": assistant_message.id if assistant_message else None,
            "metrics": final_result.to_dict() if final_result else None,
        })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/sessions/{session_id}/feedback")
async def post_feedback(request: Request, session_id: str) -> FeedbackResponse:
    container = _container(request)
    if container.store.get_session(session_id) is None:
        raise HTTPException(404, "Session not found")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(400, f"Invalid JSON body: {exc}") from exc

    try:
        body = FeedbackRequest(**(payload or {}))
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc

    message = container.store.get_message(body.message_id)
    if message is None or message.session_id != session_id:
        raise HTTPException(404, "Message not found for session")

    record = container.store.add_feedback(
        FeedbackWrite(
            session_id=session_id,
            message_id=body.message_id,
            verdict=body.verdict,
            reason=body.reason,
            note=body.note,
        )
    )
    return FeedbackResponse(
        feedback_id=record.id,
        session_id=session_id,
        stored=True,
    )
