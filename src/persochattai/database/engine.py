"""SQLAlchemy async engine + session 管理。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(db_url: str, *, pool_size: int = 5, max_overflow: int = 5) -> None:
    global _engine, _session_factory

    if not db_url.startswith('postgresql+asyncpg://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    _engine = create_async_engine(db_url, pool_size=pool_size, max_overflow=max_overflow)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info('SQLAlchemy async engine 已建立')


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info('SQLAlchemy async engine 已關閉')


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        msg = 'Session factory 尚未初始化，請先呼叫 init_engine()'
        raise RuntimeError(msg)
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — 每個 request 一個 session。"""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def run_migrations() -> None:
    """在 app 啟動時執行 Alembic migration。"""
    from alembic.config import Config

    from alembic import command

    if _engine is None:
        msg = 'Engine 尚未初始化，請先呼叫 init_engine()'
        raise RuntimeError(msg)

    def _run_upgrade(config: Config) -> None:
        command.upgrade(config, 'head')

    # Alembic migration 使用同步方式執行
    import pathlib

    project_root = pathlib.Path(__file__).resolve().parent.parent.parent.parent
    alembic_cfg = Config(str(project_root / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(project_root / 'alembic'))
    alembic_cfg.set_main_option('sqlalchemy.url', str(_engine.url))

    await _engine.dispose()

    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_upgrade, alembic_cfg)

    # 重新建立 engine（migration 可能已改 schema）
    global _session_factory
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info('Alembic migration 已完成')
