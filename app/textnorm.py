from __future__ import annotations

import re
import unicodedata


_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^0-9a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+", re.UNICODE)


def strip_accents(s: str) -> str:
    # NFKD splits accents into combining marks; drop them.
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nkfd if not unicodedata.combining(ch))


def normalize_for_match(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("đ", "d")
    s = strip_accents(s)
    s = _NON_WORD_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    s = normalize_for_match(s)
    if not s:
        return []
    return s.split(" ")

