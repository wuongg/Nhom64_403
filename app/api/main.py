from __future__ import annotations

from contextlib import asynccontextmanager

from ..settings import Settings
from .container import AppContainer, build_container
from .framework import CORSMiddleware, FastAPI, Request
from .routes import router
from .schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = getattr(app.state, "settings", None)
    if settings is None:
        settings = Settings.load()
        app.state.settings = settings

    container = build_container(settings)
    app.state.container = container
    try:
        yield
    finally:
        container.close()


def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    container: AppContainer | None = getattr(request.app.state, "container", None)
    kb_loaded = bool(container and container.core.kb_loaded)
    return HealthResponse(
        status="ok",
        kb_loaded=kb_loaded,
        openai_configured=settings.has_openai_key,
    )


def index(_: Request) -> dict:
    return {
        "name": "XanhSM Help Center AI",
        "status": "ok",
        "health": "/health",
        "api_base": "/api/v1",
    }


def debug_headers(request: Request) -> dict:
    # Development helper to diagnose browser CORS issues.
    return {"headers": dict(request.headers)}


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.load()
    app = FastAPI(title="XanhSM Help Center AI", version="1.0.0", lifespan=lifespan)
    app.state.settings = active_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.include_router(router)
    app.add_api_route("/", index, methods=["GET"])
    app.add_api_route("/debug/headers", debug_headers, methods=["GET"])
    app.add_api_route("/health", health, methods=["GET"])
    return app


app = create_app()
