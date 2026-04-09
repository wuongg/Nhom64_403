from __future__ import annotations

import json

from .llm import chat_openai, has_openai_key
from .role_tree import RoleDecision, decide_role


_ROLE_CLASSIFIER_SYSTEM = """Bạn là bộ phân loại vai trò (role classifier) cho chatbot Trung tâm hỗ trợ Xanh SM.

Nhiệm vụ: đọc tin nhắn người dùng và trả về JSON với các trường:
- role: một trong ["user","driver","merchant"]
- safety: true/false (true nếu có dấu hiệu khẩn cấp/an toàn: tai nạn, quấy rối, đe doạ, 113/115, v.v.)
- driver_type: "bike"|"taxi"|null (chỉ khi role=driver)
- confidence: số từ 0 đến 1
- reason: giải thích ngắn 1 câu

Quy tắc:
- Nếu người dùng là khách đi xe/đặt chuyến/thanh toán/tài khoản app => role="user"
- Nếu người dùng là tài xế (thu nhập, vận doanh, xe, hồ sơ tài xế, hotline tài xế...) => role="driver"
- Nếu người dùng là nhà hàng/đối tác merchant (đơn hàng, ví nhà hàng, đối soát, menu...) => role="merchant"
- Nếu safety=true nhưng không rõ role: ưu tiên role="user" trừ khi người dùng tự nhận "tôi là tài xế/nhà hàng".

Chỉ trả về JSON hợp lệ. Không kèm markdown. Không thêm chữ khác.
"""


def decide_role_with_llm(user_text: str, model: str = "gpt-4.1-mini") -> RoleDecision:
    """
    LLM-first role decision. Falls back to rule-based when no API key or parse fails.
    """
    if not has_openai_key():
        d = decide_role(user_text)
        return RoleDecision(
            role=d.role,
            safety=d.safety,
            driver_type=d.driver_type,
            reason=f"fallback(rule): {d.reason}",
        )

    raw = chat_openai(_ROLE_CLASSIFIER_SYSTEM, user_text, model=model)
    try:
        obj = json.loads(raw)
        role = obj.get("role")
        safety = bool(obj.get("safety", False))
        driver_type = obj.get("driver_type")
        reason = str(obj.get("reason", "")).strip()

        if role not in {"user", "driver", "merchant"}:
            raise ValueError("invalid role")
        if driver_type not in {None, "bike", "taxi"}:
            driver_type = None
        if role != "driver":
            driver_type = None

        return RoleDecision(
            role=role,
            safety=safety,
            driver_type=driver_type,
            reason=f"llm: {reason}",
        )
    except Exception:
        d = decide_role(user_text)
        return RoleDecision(
            role=d.role,
            safety=d.safety,
            driver_type=d.driver_type,
            reason=f"fallback(rule after llm_parse_error): {d.reason} | llm_raw={raw!r}",
        )
