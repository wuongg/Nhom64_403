from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

import httpx

from ..settings import Settings
from .types import WebSearchHit


@dataclass(frozen=True, slots=True)
class WebSearchService:
    settings: Settings

    @property
    def is_enabled(self) -> bool:
        return bool(
            self.settings.enable_web_search
            and (self.settings.serper_api_key or self.settings.serpapi_api_key)
        )

    def _search_serper_sync(self, query: str) -> tuple[WebSearchHit, ...]:
        headers = {
            "X-API-KEY": self.settings.serper_api_key or "",
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": int(self.settings.web_search_max_results),
            "gl": "vn",
            "hl": "vi",
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post("https://google.serper.dev/search", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json() or {}

        organic = data.get("organic") or []
        hits: list[WebSearchHit] = []
        for item in organic:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("link") or "").strip()
            snippet = str(item.get("snippet") or "").strip()
            if not (title and url):
                continue
            hits.append(WebSearchHit(title=title, url=url, snippet=snippet))

        return tuple(hits)

    def _search_serpapi_sync(self, query: str) -> tuple[WebSearchHit, ...]:
        # SerpAPI: https://serpapi.com/search-api
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.settings.serpapi_api_key or "",
            "gl": "vn",
            "hl": "vi",
            "num": int(self.settings.web_search_max_results),
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json() or {}

        organic = data.get("organic_results") or []
        hits: list[WebSearchHit] = []
        for item in organic:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("link") or "").strip()
            snippet = str(item.get("snippet") or item.get("snippet_highlighted_words") or "").strip()
            if not (title and url):
                continue
            hits.append(WebSearchHit(title=title, url=url, snippet=snippet))

        return tuple(hits)

    def search_sync(self, query: str) -> tuple[WebSearchHit, ...]:
        """Web search fallback.

        Supported providers:
        - Serper.dev via env SERPER_API_KEY
        - SerpAPI via env SERPAPI_API_KEY
        """
        if not self.is_enabled:
            return tuple()

        if self.settings.serper_api_key:
            try:
                return self._search_serper_sync(query)
            except httpx.HTTPStatusError as exc:
                # Common confusion: users paste a SerpAPI key into SERPER_API_KEY.
                # If Serper rejects (401/403), fall back to SerpAPI with the same key.
                status = exc.response.status_code if exc.response is not None else None
                if status in {401, 403} and not self.settings.serpapi_api_key:
                    tmp_settings = replace(
                        self.settings,
                        serpapi_api_key=self.settings.serper_api_key,
                    )
                    return WebSearchService(tmp_settings)._search_serpapi_sync(query)
                raise
        if self.settings.serpapi_api_key:
            return self._search_serpapi_sync(query)
        return tuple()

