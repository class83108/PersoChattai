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
    create_content_agent,
    get_usage_monitor,
    init_usage_monitor,
)
from persochattai.assessment.router import router as assessment_router
from persochattai.assessment.service import AssessmentService
from persochattai.config import Settings
from persochattai.content.router import router as content_router
from persochattai.content.scheduler import ContentScheduler
from persochattai.content.service import ContentService
from persochattai.conversation.manager import ConversationManager
from persochattai.conversation.router import router as conversation_router
from persochattai.conversation.stream import mount_conversation_stream
from persochattai.database.engine import dispose_engine, get_session_factory, init_engine
from persochattai.database.session_wrapper import (
    AssessmentRepositoryWrapper,
    CardRepositoryWrapper,
    ConversationRepositoryWrapper,
    ModelConfigRepositoryWrapper,
    SnapshotRepositoryWrapper,
    UsageRepositoryWrapper,
    UserRepositoryWrapper,
    VocabularyRepositoryWrapper,
)
from persochattai.frontend.router import router as frontend_router
from persochattai.usage.router import router as usage_router
from persochattai.user.router import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings

    # 1. SQLAlchemy engine + session factory
    init_engine(settings.db_url)
    factory = get_session_factory()

    # 2. Model config & usage monitor
    model_config_repo = ModelConfigRepositoryWrapper(factory)
    await model_config_repo.seed_defaults()
    app.state.model_config_repo = model_config_repo

    usage_repo = UsageRepositoryWrapper(factory)
    monitor = init_usage_monitor(
        repository=usage_repo,
        model_config_repo=model_config_repo,
    )
    await monitor.load_history()

    # 3. User repository
    user_repo = UserRepositoryWrapper(factory)
    app.state.user_repository = user_repo

    # 4. Assessment service
    assessment_repo = AssessmentRepositoryWrapper(factory)
    vocabulary_repo = VocabularyRepositoryWrapper(factory)
    snapshot_repo = SnapshotRepositoryWrapper(factory)
    assessment_service = AssessmentService(
        assessment_repo=assessment_repo,
        vocabulary_repo=vocabulary_repo,
        snapshot_repo=snapshot_repo,
        agent=None,  # type: ignore[arg-type]
    )
    assessment_service._agent = create_assessment_agent(settings, assessment_service)  # type: ignore[assignment]

    # 4. Content service
    card_repo = CardRepositoryWrapper(factory)
    app.state.card_repository = card_repo
    content_agent = create_content_agent(settings, card_repo)
    app.state.content_service = ContentService(repository=card_repo, agent=content_agent)  # type: ignore[arg-type]

    # 5. Conversation manager
    conv_repo = ConversationRepositoryWrapper(factory)

    async def _scenario_designer(source_type: str, source_ref: str) -> str:
        return f'You are an English tutor. Topic: {source_type}/{source_ref}'

    conversation_manager = ConversationManager(
        repository=conv_repo,
        scenario_designer=_scenario_designer,
        gemini_client=_create_gemini_client(settings),
        assessment_service=assessment_service,
    )
    app.state.conversation_manager = conversation_manager

    # 6. FastRTC WebRTC stream
    mount_conversation_stream(app, model=settings.gemini_model)

    # 7. Content scheduler
    scheduler = ContentScheduler()
    scheduler.start()
    app.state.content_scheduler = scheduler

    logger.info('App 啟動完成')
    yield

    scheduler.shutdown()
    await dispose_engine()
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
    app.include_router(user_router)

    @app.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/api/usage')
    async def usage() -> dict[str, Any]:
        return get_usage_monitor().get_summary()

    return app
