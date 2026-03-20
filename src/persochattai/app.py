"""FastAPI app factory。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from persochattai.agent_factory import get_usage_monitor
from persochattai.assessment.router import router as assessment_router
from persochattai.config import Settings
from persochattai.content.router import router as content_router
from persochattai.conversation.router import router as conversation_router
from persochattai.db import close_pool, init_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    await init_pool(settings.db_url)
    logger.info('App 啟動完成')
    yield
    await close_pool()
    logger.info('App 已關閉')


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings.from_env()

    app = FastAPI(
        title='PersoChattai',
        description='AI 驅動的英文練習 PWA',
        version='0.1.0',
        lifespan=_lifespan,
    )
    app.state.settings = settings

    app.include_router(content_router)
    app.include_router(conversation_router)
    app.include_router(assessment_router)

    @app.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/api/usage')
    async def usage() -> dict[str, Any]:
        return get_usage_monitor().get_summary()

    return app
