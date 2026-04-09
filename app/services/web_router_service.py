from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..llm import has_openai_key
from ..settings import Settings


_ROUTER_SYSTEM = """Bạn là bộ định tuyến tool (tool router) cho chatbot Trung tâm hỗ trợ Xanh SM.
Nhiệm vụ: quyết định có cần dùng Web Search (Google) hay chỉ dùng Knowledge Base (KB).

Nguyên tắc:
- Web Search dùng khi câu hỏi có tính "cập nhật theo thời gian" (khuyến mãi, bảng giá mới nhất, thay đổi chính sách),
  hoặc KB không đủ/không chắc để trả lời.
- Nếu dùng Web Search, phải tạo search_query bám sát Xanh SM và role (user/driver/merchant), tránh lan man.
- Nếu KB đã có câu trả lời chắc chắn, KHÔNG web search.
- Chỉ trả JSON hợp lệ, không kèm markdown.

Trả về JSON:
{
  "use_web_search": true|false,
  "prefer_web": true|false,
  "search_query": "string",
  "reason": "1 câu ngắn"
}
"""


@dataclass(frozen=True, slots=True)
class WebRouterDecision:
    use_web_search: bool
    prefer_web: bool
    search_query: str
    reason: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "use_web_search": self.use_web_search,
            "prefer_web": self.prefer_web,
            "search_query": self.search_query,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class WebRouterService:
    settings: Settings

    def decide(
        self,
        *,
        query: str,
        role: str,
        kb_summaries: list[dict[str, Any]],
        model: str,
    ) -> WebRouterDecision:
        if not (self.settings.enable_web_search and has_openai_key()):
            return WebRouterDecision(
                use_web_search=False,
                prefer_web=False,
                search_query="",
                reason="web search disabled or OPENAI_API_KEY missing",
            )

        # Keep the user message short; pass only summaries + scores.
        user_payload = {
            "query": query,
            "role": role,
            "kb_top_hits": kb_summaries[:5],
        }

        from openai import OpenAI  # type: ignore

        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": _ROUTER_SYSTEM},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        try:
            obj = json.loads(raw)
        except Exception:
            return WebRouterDecision(
                use_web_search=False,
                prefer_web=False,
                search_query="",
                reason=f"router_parse_failed: {raw[:120]}",
            )

        use_web = bool(obj.get("use_web_search", False))
        prefer_web = bool(obj.get("prefer_web", False))
        search_query = str(obj.get("search_query") or "").strip()
        reason = str(obj.get("reason") or "").strip()

        # Guardrails: force queries to stay on topic.
        if use_web:
            if not search_query:
                search_query = query
            if "xanh sm" not in search_query.lower():
                search_query = f"Xanh SM {search_query}"

        return WebRouterDecision(
            use_web_search=use_web,
            prefer_web=prefer_web and use_web,
            search_query=search_query if use_web else "",
            reason=reason or "router_decision",
        )

