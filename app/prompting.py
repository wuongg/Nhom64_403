from __future__ import annotations

from dataclasses import dataclass, field

from .kb import KBEntry
from .role_tree import RoleDecision


@dataclass(frozen=True)
class PromptBundle:
    system: str
    user: str
    debug: dict
    history: list[dict] = field(default_factory=list)


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
    history_messages: list[dict] | None = None, 
    summary: str | None = None
) -> PromptBundle:
    system_lines = [
        _role_style(decision.role),
        "Chỉ dùng thông tin có trong Knowledge Base bên dưới để hướng dẫn chính sách/nghiệp vụ; nếu thiếu thì nói rõ và chuyển nhân viên/hotline.",
        "Được phép ghi nhớ và sử dụng thông tin cá nhân (như tên gọi, sđt...) mà người dùng đã cung cấp trong hội thoại để giao tiếp tự nhiên.",
        "Không bịa số liệu/chính sách. Không yêu cầu người dùng cung cấp dữ liệu nhạy cảm (OTP, mật khẩu).",
    ]
    if decision.safety:
        system_lines.append(_safety_rules())
        
    if summary:
        system_lines.append(f"\nTóm tắt hội thoại cũ:\n{summary}")

    kb_block_lines: list[str] = []
    for i, e in enumerate(kb_hits, start=1):
        kb_block_lines.append(
            f"[KB{i}] Category: {e.category} | Topic: {e.topic} | Q: {e.question}\n{e.text}".strip()
        )

    user_msg = (
        f"Câu hỏi của người dùng:\n{query}\n\n"
        f"Knowledge Base liên quan:\n\n" + "\n\n---\n\n".join(kb_block_lines)
    )

    return PromptBundle(
        system="\n".join(system_lines),
        user=user_msg,
        debug={
            "role": decision.role,
            "safety": decision.safety,
            "driver_type": decision.driver_type,
            "reason": decision.reason,
            "contexts": [e.text for e in kb_hits],
        },
        history=history_messages or [],
    )

