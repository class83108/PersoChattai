"""asyncpg connection pool 管理。"""

from __future__ import annotations

import logging

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool(db_url: str, *, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(db_url, min_size=min_size, max_size=max_size)
    logger.info('DB connection pool 已建立', extra={'min_size': min_size, 'max_size': max_size})
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info('DB connection pool 已關閉')


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        msg = 'DB connection pool 尚未初始化，請先呼叫 init_pool()'
        raise RuntimeError(msg)
    return _pool
