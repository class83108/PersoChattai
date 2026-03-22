"""Alembic env.py — async migration 支援。"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# 確保所有 table model 都已註冊到 Base.metadata
import persochattai.database.tables  # noqa: F401
from alembic import context
from persochattai.database.base import Base

load_dotenv()

config = context.config

# 從 .env 的 DB_URL 覆寫 alembic.ini 的 sqlalchemy.url
db_url = os.getenv('DB_URL')
if db_url:
    async_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    config.set_main_option('sqlalchemy.url', async_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
