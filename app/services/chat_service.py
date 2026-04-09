from __future__ import annotations

from dataclasses import dataclass

from ..llm import ChatResult, chat_openai_with_metrics, has_openai_key
from ..prompting import build_prompt
from ..settings import Settings
from ..textnorm import normalize_for_match
from .handoff_service import HandoffService
from .kb_service import KnowledgeBaseService
from .role_service import RoleService
from .types import ChatPrepared, ChatTurnResult, HandoffDecision
from .web_search_service import WebSearchService
from .web_router_service import WebRouterService


@dataclass(frozen=True, slots=True)
class ChatService:
    settings: Settings
    role_service: RoleService
    kb_service: KnowledgeBaseService
    handoff_service: HandoffService
    web_search_service: WebSearchService
    web_router_service: WebRouterService

    def prepare(
        self,
        query: str,
        *,
        memory_summary: str | None = None,
        memory_turns: tuple[dict[str, str], ...] = tuple(),
        role_mode: str = "auto",
        role_override: str | None = None,
        k: int | None = None,
        model: str | None = None,
        preview_only: bool = False,
    ) -> ChatPrepared:
        """Run role classification, KB search, handoff eval, and prompt build.
        Does NOT call the LLM. Used by both process() and the streaming route."""
        active_model = model or self.settings.model
        top_k = k or self.settings.top_k

        decision = self.role_service.decide(
            query,
            role_mode=role_mode,
            role_override=role_override,
            model=active_model,
        )
        kb_results = self.kb_service.search(query, role=decision.role, k=top_k)
        handoff = self.handoff_service.evaluate(query, decision, kb_results)

        web_hits: tuple[dict[str, str], ...] = tuple()
        prefer_web = False
        router_debug: dict[str, object] | None = None
        if self.web_search_service.is_enabled:
            kb_summaries = [
                {
                    "score": r.score,
                    "category": r.category,
                    "topic": r.topic,
                    "question": r.question,
                }
                for r in kb_results
            ]
            router = self.web_router_service.decide(
                query=query,
                role=decision.role,
                kb_summaries=kb_summaries,
                model=active_model,
            )
            router_debug = router.to_public_dict()
            if router.use_web_search:
                try:
                    web_hits = tuple(
                        hit.to_public_dict()
                        for hit in self.web_search_service.search_sync(router.search_query)
                    )
                    prefer_web = bool(router.prefer_web and web_hits)
                    if web_hits:
                        handoff = HandoffDecision(
                            recommended=False,
                            reason="handoff deferred because web search router enabled and returned results",
                            trigger="web_search",
                        )
                except Exception:
                    web_hits = tuple()

        prompt = build_prompt(
            decision,
            query,
            [result.entry for result in kb_results],
            web_hits=web_hits,
            prefer_web=prefer_web,
            memory_summary=memory_summary,
            memory_turns=memory_turns,
        )
        debug = prompt.debug if self.settings.enable_debug_fields else {}
        if self.settings.enable_debug_fields and router_debug is not None:
            debug = dict(debug)
            debug["web_router"] = router_debug

        no_llm = preview_only or not has_openai_key()
        return ChatPrepared(
            query=query,
            role_decision=decision,
            kb_results=kb_results,
            kb_hits=tuple(result.to_hit() for result in kb_results),
            web_hits=web_hits,
            handoff=handoff,
            prompt=prompt,
            active_model=active_model,
            mode="preview" if no_llm else "answer",
            preview_only=no_llm,
            note=(
                "preview mode: explicit request"
                if preview_only
                else "preview mode: OPENAI_API_KEY is not configured"
                if no_llm
                else None
            ),
            debug=debug,
        )

    def process(
        self,
        query: str,
        *,
        memory_summary: str | None = None,
        memory_turns: tuple[dict[str, str], ...] = tuple(),
        role_mode: str = "auto",
        role_override: str | None = None,
        k: int | None = None,
        model: str | None = None,
        preview_only: bool = False,
    ) -> ChatTurnResult:
        prepared = self.prepare(
            query,
            memory_summary=memory_summary,
            memory_turns=memory_turns,
            role_mode=role_mode,
            role_override=role_override,
            k=k,
            model=model,
            preview_only=preview_only,
        )

        if prepared.preview_only:
            return ChatTurnResult(
                query=query,
                role_decision=prepared.role_decision,
                kb_results=prepared.kb_results,
                kb_hits=prepared.kb_hits,
                web_hits=prepared.web_hits,
                handoff=prepared.handoff,
                mode="preview",
                preview_only=True,
                prompt=prepared.prompt,
                answer=None,
                model=prepared.active_model,
                note=prepared.note,
                debug=prepared.debug,
            )

        try:
            answer: ChatResult = chat_openai_with_metrics(
                prepared.prompt.system,
                prepared.prompt.user,
                model=prepared.active_model,
            )
        except Exception as exc:
            failure_debug = dict(prepared.debug)
            failure_debug["llm_error"] = str(exc)
            return ChatTurnResult(
                query=query,
                role_decision=prepared.role_decision,
                kb_results=prepared.kb_results,
                kb_hits=prepared.kb_hits,
                web_hits=prepared.web_hits,
                handoff=prepared.handoff,
                mode="preview",
                preview_only=False,
                prompt=prepared.prompt,
                answer=None,
                model=prepared.active_model,
                note=f"OpenAI request failed: {exc}",
                debug=failure_debug,
            )

        return ChatTurnResult(
            query=query,
            role_decision=prepared.role_decision,
            kb_results=prepared.kb_results,
            kb_hits=prepared.kb_hits,
            web_hits=prepared.web_hits,
            handoff=prepared.handoff,
            mode="answer",
            preview_only=False,
            prompt=prepared.prompt,
            answer=answer,
            model=answer.model,
            note=None,
            debug=prepared.debug,
        )
