"""FastAPI app factory。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from persochattai.agent_factory import get_usage_monitor, init_usage_monitor
from persochattai.assessment.router import router as assessment_router
from persochattai.config import Settings
from persochattai.content.router import router as content_router
from persochattai.conversation.router import router as conversation_router
from persochattai.db import close_pool, get_pool, init_pool
from persochattai.usage.model_config_repository import ModelConfigRepository
from persochattai.usage.repository import UsageRepository
from persochattai.usage.router import router as usage_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    await init_pool(settings.db_url)
    pool = get_pool()

    model_config_repo = ModelConfigRepository(pool)
    await model_config_repo.seed_defaults()
    app.state.model_config_repo = model_config_repo

    usage_repo = UsageRepository(pool)
    monitor = init_usage_monitor(
        repository=usage_repo,
        model_config_repo=model_config_repo,
    )
    await monitor.load_history()

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
    app.include_router(usage_router)

    @app.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/api/usage')
    async def usage() -> dict[str, Any]:
        return get_usage_monitor().get_summary()

    return app
