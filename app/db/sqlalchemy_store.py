from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .contracts import (
    ChatMessageRecord,
    ChatSessionRecord,
    FeedbackWrite,
    MessageFeedbackRecord,
    MessageWrite,
    SessionDetails,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _prepare_sqlite_path(db_url: str) -> None:
    if not db_url.startswith("sqlite:///"):
        return
    path = db_url.removeprefix("sqlite:///")
    if path in {"", ":memory:"}:
        return
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    feedback: Mapped[list["MessageFeedback"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageFeedback.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True, nullable=False)
    actor: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str | None] = mapped_column(String(16), nullable=True)
    safety: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handoff_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handoff_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    kb_hits_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    feedback: Mapped["MessageFeedback | None"] = relationship(back_populates="message", uselist=False)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True, nullable=False)
    message_id: Mapped[str] = mapped_column(ForeignKey("chat_messages.id"), unique=True, index=True, nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    session: Mapped[ChatSession] = relationship(back_populates="feedback")
    message: Mapped[ChatMessage] = relationship(back_populates="feedback")


def _session_record(row: ChatSession) -> ChatSessionRecord:
    return ChatSessionRecord(
        id=row.id,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        summary=row.summary,
    )


def _message_record(row: ChatMessage) -> ChatMessageRecord:
    return ChatMessageRecord(
        id=row.id,
        session_id=row.session_id,
        actor=row.actor,
        content=row.content,
        role=row.role,
        safety=bool(row.safety),
        handoff_recommended=bool(row.handoff_recommended),
        handoff_reason=row.handoff_reason,
        model=row.model,
        latency_ms=row.latency_ms,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        total_tokens=row.total_tokens,
        cost_usd_estimate=row.cost_usd_estimate,
        kb_hits_json=row.kb_hits_json,
        created_at=row.created_at,
    )


def _feedback_record(row: MessageFeedback) -> MessageFeedbackRecord:
    return MessageFeedbackRecord(
        id=row.id,
        session_id=row.session_id,
        message_id=row.message_id,
        verdict=row.verdict,
        reason=row.reason,
        note=row.note,
        created_at=row.created_at,
    )


class SqlAlchemyChatStore:
    def __init__(self, db_url: str) -> None:
        _prepare_sqlite_path(db_url)
        self.engine = create_engine(db_url, future=True)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

    def create_all(self) -> None:
        from sqlalchemy import text
        Base.metadata.create_all(self.engine)
        if self.engine.url.drivername == "sqlite":
            with self.engine.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN summary TEXT"))
                except Exception:
                    pass

    def close(self) -> None:
        self.engine.dispose()

    @contextmanager
    def session_scope(self) -> Iterator["Session"]:
        from sqlalchemy.orm import Session

        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_session(self, status: str = "active") -> ChatSessionRecord:
        with self.session_scope() as session:
            row = ChatSession(status=status)
            session.add(row)
            session.flush()
            return _session_record(row)

    def get_session(self, session_id: str) -> ChatSessionRecord | None:
        with self.session_scope() as session:
            row = session.get(ChatSession, session_id)
            return None if row is None else _session_record(row)

    def get_session_details(self, session_id: str) -> SessionDetails | None:
        with self.session_scope() as session:
            row = session.get(ChatSession, session_id)
            if row is None:
                return None
            messages = tuple(_message_record(item) for item in row.messages)
            feedback = tuple(_feedback_record(item) for item in row.feedback)
            return SessionDetails(session=_session_record(row), messages=messages, feedback=feedback)

    def update_session_summary(self, session_id: str, summary: str) -> None:
        with self.session_scope() as session:
            row = session.get(ChatSession, session_id)
            if row is not None:
                row.summary = summary
                row.updated_at = _utcnow()
                session.flush()

    def get_message(self, message_id: str) -> ChatMessageRecord | None:
        with self.session_scope() as session:
            row = session.get(ChatMessage, message_id)
            return None if row is None else _message_record(row)

    def list_messages(self, session_id: str) -> tuple[ChatMessageRecord, ...]:
        with self.session_scope() as session:
            stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
            rows = session.execute(stmt).scalars().all()
            return tuple(_message_record(row) for row in rows)

    def list_feedback(self, session_id: str) -> tuple[MessageFeedbackRecord, ...]:
        with self.session_scope() as session:
            stmt = select(MessageFeedback).where(MessageFeedback.session_id == session_id).order_by(MessageFeedback.created_at.asc())
            rows = session.execute(stmt).scalars().all()
            return tuple(_feedback_record(row) for row in rows)

    def add_message(self, write: MessageWrite) -> ChatMessageRecord:
        with self.session_scope() as session:
            session_row = session.get(ChatSession, write.session_id)
            if session_row is None:
                raise KeyError(f"session not found: {write.session_id}")

            row = ChatMessage(
                session_id=write.session_id,
                actor=write.actor,
                content=write.content,
                role=write.role,
                safety=write.safety,
                handoff_recommended=write.handoff_recommended,
                handoff_reason=write.handoff_reason,
                model=write.model,
                latency_ms=write.latency_ms,
                input_tokens=write.input_tokens,
                output_tokens=write.output_tokens,
                total_tokens=write.total_tokens,
                cost_usd_estimate=write.cost_usd_estimate,
                kb_hits_json=None if write.kb_hits is None else json.dumps(list(write.kb_hits), ensure_ascii=False),
            )
            session.add(row)
            session_row.updated_at = _utcnow()
            session.flush()
            return _message_record(row)

    def add_feedback(self, write: FeedbackWrite) -> MessageFeedbackRecord:
        with self.session_scope() as session:
            session_row = session.get(ChatSession, write.session_id)
            if session_row is None:
                raise KeyError(f"session not found: {write.session_id}")

            row = MessageFeedback(
                session_id=write.session_id,
                message_id=write.message_id,
                verdict=write.verdict,
                reason=write.reason,
                note=write.note,
            )
            session.add(row)
            session_row.updated_at = _utcnow()
            session.flush()
            return _feedback_record(row)


def build_sqlalchemy_chat_store(db_url: str) -> SqlAlchemyChatStore:
    return SqlAlchemyChatStore(db_url)
