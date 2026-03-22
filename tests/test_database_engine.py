"""database/engine.py 單元測試。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# ---------------------------------------------------------------------------
# init_engine / dispose_engine / get_session_factory
# ---------------------------------------------------------------------------


class TestInitEngine:
    def setup_method(self) -> None:
        """每個測試前重設 engine 全域狀態。"""
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def teardown_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    @patch('persochattai.database.engine.create_async_engine')
    def test_init_engine_creates_engine_and_factory(self, mock_create: MagicMock) -> None:
        from persochattai.database.engine import _engine, _session_factory, init_engine

        assert _engine is None
        assert _session_factory is None

        init_engine('postgresql+asyncpg://localhost/test')

        mock_create.assert_called_once_with(
            'postgresql+asyncpg://localhost/test', pool_size=5, max_overflow=5
        )

        from persochattai.database.engine import _engine, _session_factory

        assert _engine is not None
        assert _session_factory is not None

    @patch('persochattai.database.engine.create_async_engine')
    def test_init_engine_auto_converts_url(self, mock_create: MagicMock) -> None:
        from persochattai.database.engine import init_engine

        init_engine('postgresql://localhost/test')

        mock_create.assert_called_once_with(
            'postgresql+asyncpg://localhost/test', pool_size=5, max_overflow=5
        )

    @patch('persochattai.database.engine.create_async_engine')
    def test_init_engine_custom_pool_params(self, mock_create: MagicMock) -> None:
        from persochattai.database.engine import init_engine

        init_engine('postgresql+asyncpg://localhost/test', pool_size=10, max_overflow=20)

        mock_create.assert_called_once_with(
            'postgresql+asyncpg://localhost/test', pool_size=10, max_overflow=20
        )


class TestDisposeEngine:
    def setup_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def teardown_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    @pytest.mark.asyncio
    async def test_dispose_engine_cleans_up(self) -> None:
        import persochattai.database.engine as mod

        mock_engine = AsyncMock()
        mod._engine = mock_engine
        mod._session_factory = MagicMock()

        from persochattai.database.engine import dispose_engine

        await dispose_engine()

        mock_engine.dispose.assert_awaited_once()
        assert mod._engine is None
        assert mod._session_factory is None

    @pytest.mark.asyncio
    async def test_dispose_engine_noop_when_not_initialized(self) -> None:
        from persochattai.database.engine import dispose_engine

        # 不應拋錯
        await dispose_engine()


class TestGetSessionFactory:
    def setup_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def teardown_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def test_raises_when_not_initialized(self) -> None:
        from persochattai.database.engine import get_session_factory

        with pytest.raises(RuntimeError, match='尚未初始化'):
            get_session_factory()

    @patch('persochattai.database.engine.create_async_engine')
    def test_returns_factory_after_init(self, mock_create: MagicMock) -> None:
        from persochattai.database.engine import get_session_factory, init_engine

        init_engine('postgresql+asyncpg://localhost/test')
        factory = get_session_factory()
        assert factory is not None


# ---------------------------------------------------------------------------
# get_session (FastAPI dependency)
# ---------------------------------------------------------------------------


class TestGetSession:
    def setup_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def teardown_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    @pytest.mark.asyncio
    async def test_get_session_yields_session(self) -> None:
        import persochattai.database.engine as mod

        mock_session = AsyncMock(spec=AsyncSession)

        mock_factory = MagicMock(spec=async_sessionmaker)
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_ctx

        mod._session_factory = mock_factory

        from persochattai.database.engine import get_session

        sessions = []
        async for s in get_session():
            sessions.append(s)

        assert len(sessions) == 1
        assert sessions[0] is mock_session


# ---------------------------------------------------------------------------
# run_migrations
# ---------------------------------------------------------------------------


class TestRunMigrations:
    def setup_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    def teardown_method(self) -> None:
        import persochattai.database.engine as mod

        mod._engine = None
        mod._session_factory = None

    @pytest.mark.asyncio
    async def test_run_migrations_raises_when_no_engine(self) -> None:
        from persochattai.database.engine import run_migrations

        with pytest.raises(RuntimeError, match='尚未初始化'):
            await run_migrations()
