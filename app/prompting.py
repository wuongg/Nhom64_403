from __future__ import annotations

from dataclasses import dataclass

from .kb import KBEntry
from .role_tree import RoleDecision


@dataclass(frozen=True)
class PromptBundle:
    system: str
    user: str
    debug: dict


def _role_style(role: str) -> str:
    if role == "merchant":
        return (
            "Bạn là trợ lý hỗ trợ cho Đối tác Nhà hàng trên Xanh SM Merchant. "
            "Trả lời ngắn gọn theo bước, ưu tiên hướng dẫn thao tác trong app và kênh liên hệ (hotline/email) nếu có."
        )
    if role == "driver":
        return (
            "Bạn là trợ lý hỗ trợ cho Tài xế Xanh SM (Taxi/Bike). "
            "Trả lời rõ ràng, theo bước, ưu tiên kênh hỗ trợ tài xế và địa chỉ trung tâm khi cần."
        )
    return (
        "Bạn là trợ lý Trung tâm hỗ trợ Xanh SM cho Người dùng. "
        "Trả lời ngắn gọn theo bước, không suy đoán dữ liệu cá nhân/chuyến đi nếu không có."
    )


def _safety_rules() -> str:
    return (
        "Ưu tiên an toàn: nếu người dùng có dấu hiệu khẩn cấp/đe doạ an toàn, "
        "hãy đưa hành động ngay (rời nơi nguy hiểm, gọi 113/115 khi phù hợp, hotline hỗ trợ), "
        "sau đó mới hỏi thêm thông tin tối thiểu."
    )


def build_prompt(
    decision: RoleDecision,
    query: str,
    kb_hits: list[KBEntry],
    *,
    web_hits: tuple[dict[str, str], ...] = tuple(),
    prefer_web: bool = False,
    memory_summary: str | None = None,
    memory_turns: tuple[dict[str, str], ...] = tuple(),
) -> PromptBundle:
    system_lines = [
        _role_style(decision.role),
        "Ưu tiên Knowledge Base. Nếu Knowledge Base không đủ thông tin, bạn có thể tham khảo phần Web Search (nếu có) "
        "nhưng chỉ dùng khi nội dung liên quan trực tiếp đến Xanh SM và có nguồn rõ ràng. Nếu không đủ tin cậy/liên quan, "
        "hãy nói rõ và hướng dẫn chuyển nhân viên/hotline.",
        "Không bịa số liệu/chính sách. Không yêu cầu người dùng cung cấp dữ liệu nhạy cảm (OTP, mật khẩu).",
    ]
    if prefer_web and web_hits:
        system_lines.append(
            "Với câu hỏi dạng cập nhật/khuyến mãi/mới nhất: nếu có Web Search bên dưới, hãy trả lời dựa trên Web Search "
            "và đính kèm 1-3 nguồn (URL). Không được trả lời kiểu 'không có thông tin' khi Web Search đã có kết quả."
        )
    if decision.safety:
        system_lines.append(_safety_rules())

    kb_block_lines: list[str] = []
    for i, e in enumerate(kb_hits, start=1):
        kb_block_lines.append(
            f"[KB{i}] Category: {e.category} | Topic: {e.topic} | Q: {e.question}\n{e.text}".strip()
        )

    user_msg = f"Câu hỏi của người dùng:\n{query}\n\n"

    if memory_summary or memory_turns:
        user_msg += "Ngữ cảnh hội thoại (memory):\n"
        if memory_summary:
            user_msg += f"- Tóm tắt trước đó:\n{memory_summary.strip()}\n"
        if memory_turns:
            user_msg += "- 5 lượt gần nhất:\n"
            for t in memory_turns:
                role = t.get("role", "")
                content = t.get("content", "")
                user_msg += f"  - {role}: {content}\n"
        user_msg += "\n"

    # For time-sensitive queries, show web sources first to reduce the chance the model ignores them.
    if prefer_web and web_hits:
        web_lines: list[str] = []
        for i, hit in enumerate(web_hits, start=1):
            web_lines.append(
                f"[WEB{i}] {hit.get('title','')}\nURL: {hit.get('url','')}\nSnippet: {hit.get('snippet','')}".strip()
            )
        user_msg += (
            "Web Search (ưu tiên, chỉ dùng nếu liên quan Xanh SM):\n\n"
            + "\n\n---\n\n".join(web_lines)
            + "\n\n"
        )

    user_msg += "Knowledge Base liên quan:\n\n" + "\n\n---\n\n".join(kb_block_lines)

    if web_hits:
        # If we didn't already put web first, append as fallback.
        if not (prefer_web and web_hits):
            web_lines: list[str] = []
            for i, hit in enumerate(web_hits, start=1):
                web_lines.append(
                    f"[WEB{i}] {hit.get('title','')}\nURL: {hit.get('url','')}\nSnippet: {hit.get('snippet','')}".strip()
                )
            user_msg += "\n\nWeb Search (tham khảo, chỉ dùng nếu liên quan Xanh SM):\n\n" + "\n\n---\n\n".join(web_lines)

    return PromptBundle(
        system="\n".join(system_lines),
        user=user_msg,
        debug={
            "role": decision.role,
            "safety": decision.safety,
            "driver_type": decision.driver_type,
            "reason": decision.reason,
            "contexts": [e.text for e in kb_hits],
            "web_hits": list(web_hits),
            "memory": {
                "summary": memory_summary,
                "turns": list(memory_turns),
            },
        },
    )

