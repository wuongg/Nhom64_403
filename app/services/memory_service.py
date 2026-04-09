from __future__ import annotations

from dataclasses import dataclass

from ..db.contracts import ChatMessageRecord
from ..llm import chat_openai_with_metrics, has_openai_key
from ..settings import Settings


_MEMORY_SYSTEM = """Bạn là bộ nhớ hội thoại (conversation memory) cho chatbot CSKH Xanh SM.
Hãy tóm tắt hội thoại trước đó để dùng làm ngữ cảnh cho câu hỏi tiếp theo.

Yêu cầu:
- Tối đa 6-10 gạch đầu dòng, ngắn gọn.
- Giữ lại: mục tiêu/vấn đề chính của khách, ràng buộc quan trọng, thông tin đã cung cấp, quyết định đã chốt.
- Không thêm thông tin mới. Không suy đoán. Không lưu dữ liệu nhạy cảm (OTP, mật khẩu, số thẻ).
- Nếu không có gì đáng nhớ, trả chuỗi rỗng.
"""


@dataclass(frozen=True, slots=True)
class MemoryBundle:
    summary: str | None
    turns: tuple[dict[str, str], ...]  # last N messages for prompt


@dataclass(frozen=True, slots=True)
class MemoryService:
    settings: Settings

    def build(
        self,
        messages: tuple[ChatMessageRecord, ...],
        *,
        last_messages: int = 10,
    ) -> tuple[MemoryBundle, str | None]:
        """Return (memory_bundle, updated_summary_or_none).

        - Keeps last `last_messages` (user/assistant only) verbatim in turns.
        - Summarizes older messages (optionally plus existing summary).
        """
        # Extract newest stored summary (if any)
        summaries = [m for m in messages if m.actor == "memory"]
        existing_summary = summaries[-1].content.strip() if summaries else ""

        chat_msgs = [m for m in messages if m.actor in {"user", "assistant"}]
        if not chat_msgs:
            return MemoryBundle(summary=None, turns=tuple()), None

        recent = chat_msgs[-last_messages:]
        turns = tuple({"role": m.actor, "content": m.content} for m in recent)

        older = chat_msgs[:-last_messages]
        if not older:
            return MemoryBundle(summary=existing_summary or None, turns=turns), None

        if not has_openai_key():
            # Can't summarize without LLM; still provide recent turns.
            return MemoryBundle(summary=existing_summary or None, turns=turns), None

        # Build summarization input: existing summary + older messages
        parts: list[str] = []
        if existing_summary:
            parts.append(f"TÓM TẮT TRƯỚC ĐÓ:\n{existing_summary}")
        for m in older:
            parts.append(f"{m.actor.upper()}: {m.content}")
        user = "\n".join(parts)

        result = chat_openai_with_metrics(_MEMORY_SYSTEM, user, model=self.settings.model)
        new_summary = (result.text or "").strip()
        if not new_summary:
            new_summary = ""

        return MemoryBundle(summary=new_summary or None, turns=turns), (new_summary or "")

