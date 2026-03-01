import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routes import get_bot_manager
from app.api.routes import router as bots_router
from app.application.bot_manager import BotManager
from app.core.config import BotSettings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def _get_bot_manager(request: Request) -> BotManager:
    return request.app.state.bot_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = BotSettings()
    app.state.bot_manager = BotManager(settings=app.state.settings)
    try:
        yield
    finally:
        await app.state.bot_manager.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.dependency_overrides[get_bot_manager] = _get_bot_manager
    app.include_router(bots_router)
    return app


app = create_app()
