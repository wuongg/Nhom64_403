from __future__ import annotations

from dataclasses import dataclass

from ..settings import Settings
from .chat_service import ChatService
from .handoff_service import HandoffService
from .kb_service import KnowledgeBaseService
from .memory_service import MemoryService
from .role_service import RoleService
from .web_search_service import WebSearchService
from .web_router_service import WebRouterService


@dataclass(frozen=True, slots=True)
class CoreServices:
    settings: Settings
    role_service: RoleService
    kb_service: KnowledgeBaseService
    handoff_service: HandoffService
    chat_service: ChatService
    web_search_service: WebSearchService
    web_router_service: WebRouterService
    memory_service: MemoryService

    @property
    def kb_loaded(self) -> bool:
        return self.kb_service.is_loaded

    @property
    def openai_configured(self) -> bool:
        return self.settings.has_openai_key


def build_core_services(settings: Settings | None = None) -> CoreServices:
    active_settings = settings or Settings.load()
    active_settings.apply_to_env()

    role_service = RoleService(active_settings)
    kb_service = KnowledgeBaseService.load(active_settings.raw_dir)
    handoff_service = HandoffService()
    web_search_service = WebSearchService(active_settings)
    web_router_service = WebRouterService(active_settings)
    memory_service = MemoryService(active_settings)
    chat_service = ChatService(
        settings=active_settings,
        role_service=role_service,
        kb_service=kb_service,
        handoff_service=handoff_service,
        web_search_service=web_search_service,
        web_router_service=web_router_service,
    )
    return CoreServices(
        settings=active_settings,
        role_service=role_service,
        kb_service=kb_service,
        handoff_service=handoff_service,
        chat_service=chat_service,
        web_search_service=web_search_service,
        web_router_service=web_router_service,
        memory_service=memory_service,
    )
