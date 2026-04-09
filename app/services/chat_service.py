from __future__ import annotations

from dataclasses import dataclass

from ..llm import ChatResult, chat_openai_with_metrics, has_openai_key
from ..prompting import build_prompt
from ..settings import Settings
from .handoff_service import HandoffService
from .kb_service import KnowledgeBaseService
from .role_service import RoleService
from ..db.contracts import SessionDetails
from .types import ChatPrepared, ChatTurnResult


@dataclass(frozen=True, slots=True)
class ChatService:
    settings: Settings
    role_service: RoleService
    kb_service: KnowledgeBaseService
    handoff_service: HandoffService

    def prepare(
        self,
        query: str,
        *,
        role_mode: str = "auto",
        role_override: str | None = None,
        k: int | None = None,
        model: str | None = None,
        preview_only: bool = False,
        session_details: SessionDetails | None = None,
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

        new_summary = None
        history_messages = []
        summary_text = None
        if session_details:
            summary_text = session_details.session.summary
            past_messages = [m for m in session_details.messages if m.actor in ("user", "assistant")]
            if len(past_messages) > 10:
                messages_to_summarize = past_messages[:-10]
                kept_messages = past_messages[-10:]
                
                summary_prompt = "Bạn là một trợ lý thông minh. Hãy tóm tắt ngắn gọn nội dung cốt lõi của phần bối cảnh cũ sau đây."
                if summary_text:
                    summary_prompt += f"\nBối cảnh cũ:\n{summary_text}"
                summary_prompt += "\nCác tin nhắn mới cần tóm tắt thêm:"
                
                for m in messages_to_summarize:
                    actor_name = "Người dùng" if m.actor == "user" else "Trợ lý"
                    summary_prompt += f"\n{actor_name}: {m.content}"
                    
                # Do not call API if Open_API key is not configured
                if has_openai_key():
                    try:
                        summary_result = chat_openai_with_metrics(summary_prompt, "Hãy tóm tắt ngắn gọn nội dung trên.", model=active_model)
                        new_summary = summary_result.text
                        summary_text = new_summary
                    except Exception as e:
                        print(f"Summarization error: {e}")
            else:
                kept_messages = past_messages
                
            history_messages = [{"role": m.actor, "content": m.content} for m in kept_messages]

        prompt = build_prompt(
            decision, 
            query, 
            [result.entry for result in kb_results], 
            history_messages=history_messages, 
            summary=summary_text
        )
        debug = prompt.debug if self.settings.enable_debug_fields else {}

        no_llm = preview_only or not has_openai_key()
        return ChatPrepared(
            query=query,
            role_decision=decision,
            kb_results=kb_results,
            kb_hits=tuple(result.to_hit() for result in kb_results),
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
            new_summary=new_summary,
        )

    def process(
        self,
        query: str,
        *,
        role_mode: str = "auto",
        role_override: str | None = None,
        k: int | None = None,
        model: str | None = None,
        preview_only: bool = False,
        session_details: SessionDetails | None = None,
    ) -> ChatTurnResult:
        prepared = self.prepare(
            query,
            role_mode=role_mode,
            role_override=role_override,
            k=k,
            model=model,
            preview_only=preview_only,
            session_details=session_details,
        )

        if prepared.preview_only:
            return ChatTurnResult(
                query=query,
                role_decision=prepared.role_decision,
                kb_results=prepared.kb_results,
                kb_hits=prepared.kb_hits,
                handoff=prepared.handoff,
                mode="preview",
                preview_only=True,
                prompt=prepared.prompt,
                answer=None,
                model=prepared.active_model,
                note=prepared.note,
                debug=prepared.debug,
                new_summary=prepared.new_summary,
            )

        try:
            answer: ChatResult = chat_openai_with_metrics(
                prepared.prompt.system,
                prepared.prompt.user,
                history=prepared.prompt.history,
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
                handoff=prepared.handoff,
                mode="preview",
                preview_only=False,
                prompt=prepared.prompt,
                answer=None,
                model=prepared.active_model,
                note=f"OpenAI request failed: {exc}",
                debug=failure_debug,
                new_summary=prepared.new_summary,
            )

        return ChatTurnResult(
            query=query,
            role_decision=prepared.role_decision,
            kb_results=prepared.kb_results,
            kb_hits=prepared.kb_hits,
            handoff=prepared.handoff,
            mode="answer",
            preview_only=False,
            prompt=prepared.prompt,
            answer=answer,
            model=answer.model,
            note=None,
            debug=prepared.debug,
            new_summary=prepared.new_summary,
        )
