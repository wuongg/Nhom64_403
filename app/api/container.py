from __future__ import annotations

from dataclasses import dataclass

from ..db.sqlalchemy_store import SqlAlchemyChatStore
from ..services import CoreServices, build_core_services
from ..settings import Settings


@dataclass(frozen=True, slots=True)
class AppContainer:
    settings: Settings
    core: CoreServices
    store: SqlAlchemyChatStore

    @property
    def kb_service(self):
        return self.core.kb_service

    @property
    def role_service(self):
        return self.core.role_service

    @property
    def handoff_service(self):
        return self.core.handoff_service

    @property
    def chat_service(self):
        return self.core.chat_service

    @property
    def memory_service(self):
        return self.core.memory_service

    def close(self) -> None:
        self.store.close()


def build_container(settings: Settings) -> AppContainer:
    core = build_core_services(settings)
    store = SqlAlchemyChatStore(settings.db_url)
    store.create_all()
    return AppContainer(settings=settings, core=core, store=store)
