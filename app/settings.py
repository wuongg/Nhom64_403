from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from dotenv import load_dotenv


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    items = [item.strip() for item in value.split(",")]
    return tuple(item for item in items if item)


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    openai_api_key: str | None = None
    model: str = "gpt-4o-mini"
    raw_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1] / "raw")
    db_url: str = "sqlite:///./xanhsm_helpcenter.db"
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    top_k: int = 5
    enable_debug_fields: bool = True
    enable_web_search: bool = False
    serper_api_key: str | None = None
    serpapi_api_key: str | None = None
    web_search_max_results: int = 5
    web_search_kb_score_threshold: int = 2

    @classmethod
    def load(cls, env_file: str | Path | None = None) -> "Settings":
        load_dotenv(dotenv_path=env_file, override=False)
        settings = cls.from_env()
        settings.apply_to_env()
        return settings

    @classmethod
    def from_env(cls) -> "Settings":
        raw_dir = os.getenv("RAW_DIR")
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            model=os.getenv("MODEL") or "gpt-4o-mini",
            raw_dir=Path(raw_dir).expanduser().resolve() if raw_dir else Path(__file__).resolve().parents[1] / "raw",
            db_url=os.getenv("DB_URL") or "sqlite:///./xanhsm_helpcenter.db",
            cors_origins=_parse_csv(
                os.getenv("CORS_ORIGINS"),
                (
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ),
            ),
            top_k=max(1, _parse_int(os.getenv("TOP_K"), 5)),
            enable_debug_fields=_parse_bool(os.getenv("ENABLE_DEBUG_FIELDS"), True),
            enable_web_search=_parse_bool(os.getenv("ENABLE_WEB_SEARCH"), False),
            serper_api_key=os.getenv("SERPER_API_KEY") or None,
            serpapi_api_key=os.getenv("SERPAPI_API_KEY") or None,
            web_search_max_results=max(1, _parse_int(os.getenv("WEB_SEARCH_MAX_RESULTS"), 5)),
            web_search_kb_score_threshold=max(0, _parse_int(os.getenv("WEB_SEARCH_KB_SCORE_THRESHOLD"), 2)),
        )

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)

    def apply_to_env(self) -> None:
        if self.openai_api_key is not None:
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
        os.environ["MODEL"] = self.model
        os.environ["RAW_DIR"] = str(self.raw_dir)
        os.environ["DB_URL"] = self.db_url
        os.environ["CORS_ORIGINS"] = ",".join(self.cors_origins)
        os.environ["TOP_K"] = str(self.top_k)
        os.environ["ENABLE_DEBUG_FIELDS"] = "true" if self.enable_debug_fields else "false"
        os.environ["ENABLE_WEB_SEARCH"] = "true" if self.enable_web_search else "false"
        if self.serper_api_key is not None:
            os.environ["SERPER_API_KEY"] = self.serper_api_key
        if self.serpapi_api_key is not None:
            os.environ["SERPAPI_API_KEY"] = self.serpapi_api_key
        os.environ["WEB_SEARCH_MAX_RESULTS"] = str(self.web_search_max_results)
        os.environ["WEB_SEARCH_KB_SCORE_THRESHOLD"] = str(self.web_search_kb_score_threshold)

    def with_overrides(self, **changes: object) -> "Settings":
        normalized = dict(changes)
        if "raw_dir" in normalized and normalized["raw_dir"] is not None:
            normalized["raw_dir"] = Path(normalized["raw_dir"]).expanduser().resolve()
        if "top_k" in normalized and normalized["top_k"] is not None:
            try:
                normalized["top_k"] = max(1, int(normalized["top_k"]))
            except (TypeError, ValueError):
                normalized.pop("top_k", None)
        if "cors_origins" in normalized and normalized["cors_origins"] is not None:
            value = normalized["cors_origins"]
            if isinstance(value, str):
                normalized["cors_origins"] = _parse_csv(value, self.cors_origins)
            else:
                normalized["cors_origins"] = tuple(str(item).strip() for item in value if str(item).strip())
        return replace(self, **normalized)
