"""FastAPI app factory。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from persochattai.agent_factory import (
    create_assessment_agent,
    get_usage_monitor,
    init_usage_monitor,
)
from persochattai.assessment.repository import AssessmentRepository
from persochattai.assessment.router import router as assessment_router
from persochattai.assessment.service import AssessmentService
from persochattai.assessment.snapshot_repository import LevelSnapshotRepository
from persochattai.assessment.vocabulary_repository import UserVocabularyRepository
from persochattai.config import Settings
from persochattai.content.router import router as content_router
from persochattai.content.scheduler import ContentScheduler
from persochattai.conversation.manager import ConversationManager
from persochattai.conversation.repository import ConversationRepository
from persochattai.conversation.router import router as conversation_router
from persochattai.conversation.stream import mount_conversation_stream
from persochattai.db import close_pool, get_pool, init_pool
from persochattai.frontend.router import router as frontend_router
from persochattai.usage.model_config_repository import ModelConfigRepository
from persochattai.usage.repository import UsageRepository
from persochattai.usage.router import router as usage_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    await init_pool(settings.db_url)
    pool = get_pool()

    # Model config & usage monitor
    model_config_repo = ModelConfigRepository(pool)
    await model_config_repo.seed_defaults()
    app.state.model_config_repo = model_config_repo

    usage_repo = UsageRepository(pool)
    monitor = init_usage_monitor(
        repository=usage_repo,
        model_config_repo=model_config_repo,
    )
    await monitor.load_history()

    # Assessment service
    assessment_repo = AssessmentRepository(pool)
    vocabulary_repo = UserVocabularyRepository(pool)
    snapshot_repo = LevelSnapshotRepository(pool)
    assessment_service = AssessmentService(
        assessment_repo=assessment_repo,
        vocabulary_repo=vocabulary_repo,
        snapshot_repo=snapshot_repo,
        agent=None,  # type: ignore[arg-type]
    )
    assessment_service._agent = create_assessment_agent(settings, assessment_service)  # type: ignore[assignment]

    # Conversation manager
    conv_repo = ConversationRepository(pool)

    async def _scenario_designer(source_type: str, source_ref: str) -> str:
        # Placeholder: 未來由 BYOA Agent 生成 system instruction
        return f'You are an English tutor. Topic: {source_type}/{source_ref}'

    conversation_manager = ConversationManager(
        repository=conv_repo,
        scenario_designer=_scenario_designer,
        gemini_client=_create_gemini_client(settings),
        assessment_service=assessment_service,
    )
    app.state.conversation_manager = conversation_manager

    # FastRTC WebRTC stream
    mount_conversation_stream(app, model=settings.gemini_model)

    # Content scheduler
    scheduler = ContentScheduler()
    scheduler.start()
    app.state.content_scheduler = scheduler

    logger.info('App 啟動完成')
    yield

    scheduler.shutdown()
    await close_pool()
    logger.info('App 已關閉')


def _create_gemini_client(settings: Settings) -> Any:
    """建立 Gemini client。"""
    try:
        import google.genai as genai

        return genai.Client(api_key=settings.gemini_api_key)
    except ImportError:
        from unittest.mock import MagicMock

        logger.warning('google-genai 未安裝，使用 mock client')
        return MagicMock()


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

    # Static files
    static_dir = Path(__file__).resolve().parent.parent.parent / 'static'
    app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')

    # Routers
    app.include_router(frontend_router)
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
