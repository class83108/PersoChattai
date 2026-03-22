"""整合測試共用 fixtures — 使用真實 PostgreSQL。"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from persochattai.database.base import Base
from persochattai.database.tables import (  # noqa: F401 — 確保所有 table 被 import 到 metadata
    ApiUsageTable,
    AssessmentTable,
    CardTable,
    ConversationTable,
    ModelConfigTable,
    UserLevelSnapshotTable,
    UserTable,
    UserVocabularyTable,
)

load_dotenv()

_TEST_DB_URL = os.environ.get('TEST_DB_URL', '')
if not _TEST_DB_URL:
    _base_url = os.environ.get('DB_URL', '')
    if _base_url and '://' in _base_url:
        _TEST_DB_URL = _base_url.rsplit('/', 1)[0] + '/persochattai_test'

_HAS_DB = bool(_TEST_DB_URL and '://' in _TEST_DB_URL)
_ASYNC_URL = _TEST_DB_URL.replace('postgresql://', 'postgresql+asyncpg://', 1) if _HAS_DB else ''

pytestmark = pytest.mark.skipif(not _HAS_DB, reason='TEST_DB_URL 或 DB_URL 未設定')

_DB_CREATED = False


async def _ensure_test_db() -> None:
    """確保 test DB 存在（只執行一次）。"""
    global _DB_CREATED
    if _DB_CREATED:
        return

    base_url = _ASYNC_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_async_engine(base_url, isolation_level='AUTOCOMMIT')
    async with admin_engine.connect() as conn:
        await conn.execute(
            text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'persochattai_test' AND pid <> pg_backend_pid()
            """)
        )
        await conn.execute(text('DROP DATABASE IF EXISTS persochattai_test'))
        await conn.execute(text('CREATE DATABASE persochattai_test'))
    await admin_engine.dispose()

    # 建表
    engine = create_async_engine(_ASYNC_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    _DB_CREATED = True


# 按 FK 依賴反序排列
_TABLE_NAMES = [
    'user_level_snapshots',
    'user_vocabulary',
    'assessments',
    'api_usage',
    'model_config',
    'conversations',
    'cards',
    'users',
]


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    """每個測試一個 engine，避免 event loop 問題。"""
    if not _HAS_DB:
        pytest.skip('TEST_DB_URL 或 DB_URL 未設定')
    await _ensure_test_db()
    test_engine = create_async_engine(_ASYNC_URL, pool_size=5, max_overflow=0)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """每個測試一個獨立 session，測試前清表確保隔離。"""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()

    for table in _TABLE_NAMES:
        await session.execute(text(f'DELETE FROM {table}'))
    await session.commit()

    yield session

    await session.close()
