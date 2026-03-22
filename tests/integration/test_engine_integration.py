"""database/engine.py 整合測試 — 接真實 PostgreSQL。"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

_DB_URL = os.environ.get('DB_URL', '')
pytestmark = pytest.mark.skipif(not _DB_URL or '://' not in _DB_URL, reason='DB_URL 未設定')


class TestInitEngineIntegration:
    """驗證 init_engine → get_session_factory → dispose_engine 完整生命週期。"""

    @pytest.mark.asyncio
    async def test_engine_lifecycle(self) -> None:
        import persochattai.database.engine as mod

        # 確保乾淨狀態
        mod._engine = None
        mod._session_factory = None

        try:
            mod.init_engine(_DB_URL)

            factory = mod.get_session_factory()
            async with factory() as session:
                result = await session.execute(text('SELECT 1'))
                assert result.scalar() == 1

            await mod.dispose_engine()
            assert mod._engine is None
            assert mod._session_factory is None
        finally:
            # 確保清理
            if mod._engine is not None:
                await mod.dispose_engine()


class TestRunMigrationsIntegration:
    """驗證 Alembic migration 能在真實 DB 上執行。"""

    @pytest.mark.asyncio
    async def test_run_migrations_creates_tables(self, engine) -> None:
        """用 test DB engine 驗證 metadata 建表後表存在。"""
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]

        expected = [
            'api_usage',
            'assessments',
            'cards',
            'conversations',
            'model_config',
            'user_level_snapshots',
            'user_vocabulary',
            'users',
        ]
        for table in expected:
            assert table in tables, f'缺少表 {table}'
