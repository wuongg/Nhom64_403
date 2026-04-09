from __future__ import annotations

from dataclasses import dataclass

from .textnorm import normalize_for_match


@dataclass(frozen=True)
class RoleDecision:
    role: str  # "user" | "driver" | "merchant"
    safety: bool
    driver_type: str | None = None  # "taxi" | "bike" | None
    reason: str = ""


_SAFETY_KEYWORDS = [
    "tai nan",
    "su co nghiem trong",
    "khong an toan",
    "quay roi",
    "cong an",
    "cap cuu",
    "113",
    "115",
    "bi tan cong",
    "de doa",
]

_MERCHANT_KEYWORDS = [
    "nha hang",
    "quan an",
    "merchant",
    "doi tac nha hang",
    "don hang",
    "thuc don",
    "vi nha hang",
    "doi soat",
    "hoa hong",
    "rut tien",
    "khuyen mai",
    "tao khuyen mai",
]

_DRIVER_KEYWORDS = [
    "tai xe",
    "chay xe",
    "bike",
    "taxi",
    "thu nhap",
    "luong",
    "thuong",
    "coc xe",
    "bao duong",
    "dao tao",
    "ho tro tai xe",
    "cuu ho",
]

_DRIVER_TAXI_KEYWORDS = ["taxi", "o to", "oto", "xe taxi"]
_DRIVER_BIKE_KEYWORDS = ["bike", "xe may", "xe may dien", "xe 2 banh"]

_SELF_IDENTIFY_DRIVER = [
    "toi la tai xe",
    "em la tai xe",
    "minh la tai xe",
    "toi dang la tai xe",
    "toi la tai xe xanh sm",
]

_SELF_IDENTIFY_MERCHANT = [
    "toi la nha hang",
    "em la nha hang",
    "minh la nha hang",
    "toi la doi tac nha hang",
    "em la doi tac nha hang",
]


def _contains_any(haystack: str, phrases: list[str]) -> bool:
    return any(p in haystack for p in phrases)


def decide_role(user_text: str) -> RoleDecision:
    s = normalize_for_match(user_text)

    safety = _contains_any(s, _SAFETY_KEYWORDS)
    if safety:
        # Safety takes priority for UX.
        # In safety situations, default to "user" unless the speaker self-identifies as driver/merchant.
        role = "user"
        reason = "matched safety keywords"
        if _contains_any(s, _SELF_IDENTIFY_MERCHANT):
            role = "merchant"
            reason += " + self-identified merchant"
        elif _contains_any(s, _SELF_IDENTIFY_DRIVER):
            role = "driver"
            reason += " + self-identified driver"

        driver_type = None
        if role == "driver":
            if _contains_any(s, _DRIVER_TAXI_KEYWORDS):
                driver_type = "taxi"
            elif _contains_any(s, _DRIVER_BIKE_KEYWORDS):
                driver_type = "bike"
        return RoleDecision(role=role, safety=True, driver_type=driver_type, reason=reason)

    if _contains_any(s, _MERCHANT_KEYWORDS):
        return RoleDecision(role="merchant", safety=False, reason="matched merchant keywords")

    if _contains_any(s, _DRIVER_KEYWORDS):
        driver_type = None
        if _contains_any(s, _DRIVER_TAXI_KEYWORDS):
            driver_type = "taxi"
        elif _contains_any(s, _DRIVER_BIKE_KEYWORDS):
            driver_type = "bike"
        return RoleDecision(role="driver", safety=False, driver_type=driver_type, reason="matched driver keywords")

    return RoleDecision(role="user", safety=False, reason="default")

