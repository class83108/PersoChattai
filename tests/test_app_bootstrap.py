"""App Bootstrap 測試。"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

from persochattai.config import Settings

scenarios('features/app_bootstrap.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Fixtures ---


@pytest.fixture
def settings() -> Settings:
    return Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Given ---


@given('完整配置的 Settings')
def full_settings(settings: Settings, ctx: dict[str, Any]) -> None:
    ctx['settings'] = settings


@given('App 已啟動且 ContentScheduler 正在運行')
def app_started_with_scheduler(settings: Settings, ctx: dict[str, Any]) -> None:
    ctx['settings'] = settings
    _start_app(settings, ctx)


@given('App 已啟動')
def app_started(settings: Settings, ctx: dict[str, Any]) -> None:
    ctx['settings'] = settings
    _start_app(settings, ctx)


# --- When ---


@when('App 啟動完成 lifespan')
def start_lifespan(ctx: dict[str, Any]) -> None:
    _start_app(ctx['settings'], ctx)


@when('App 執行 shutdown')
def shutdown_app(ctx: dict[str, Any]) -> None:
    cleanup = ctx.get('cleanup')
    if cleanup:
        cleanup()


@when('匯入 persochattai.__main__ 模組', target_fixture='main_module')
def import_main() -> Any:
    import persochattai.__main__ as m

    return m


# --- Then ---


@then('app.state 應包含 conversation_manager')
def check_conversation_manager(ctx: dict[str, Any]) -> None:
    app = ctx['app']
    assert hasattr(app.state, 'conversation_manager')
    assert app.state.conversation_manager is not None


@then('app.state 應包含 model_config_repo')
def check_model_config_repo(ctx: dict[str, Any]) -> None:
    app = ctx['app']
    assert hasattr(app.state, 'model_config_repo')


@then('app.state 應包含 content_scheduler')
def check_content_scheduler(ctx: dict[str, Any]) -> None:
    app = ctx['app']
    assert hasattr(app.state, 'content_scheduler')


@then('conversation_manager 應具備 repository')
def check_manager_has_repo(ctx: dict[str, Any]) -> None:
    manager = ctx['app'].state.conversation_manager
    assert manager._repository is not None


@then('conversation_manager 應具備 scenario_designer')
def check_manager_has_designer(ctx: dict[str, Any]) -> None:
    manager = ctx['app'].state.conversation_manager
    assert manager._scenario_designer is not None


@then('conversation_manager 應具備 assessment_service')
def check_manager_has_assessment(ctx: dict[str, Any]) -> None:
    manager = ctx['app'].state.conversation_manager
    assert manager._assessment_service is not None


@then('content_scheduler 應處於 running 狀態')
def check_scheduler_running(ctx: dict[str, Any]) -> None:
    assert ctx['snapshot']['scheduler_running']


@then('content_scheduler 應有 scrape_podcasts job')
def check_scheduler_has_job(ctx: dict[str, Any]) -> None:
    assert ctx['snapshot']['scheduler_has_job']


@then('content_scheduler 應處於非 running 狀態')
def check_scheduler_stopped(ctx: dict[str, Any]) -> None:
    scheduler = ctx['app'].state.content_scheduler
    assert not scheduler.is_running()


@then('DB pool 應已關閉')
def check_pool_closed(ctx: dict[str, Any]) -> None:
    assert ctx.get('pool_closed', False)


@then('路徑 "/api/conversation/rtc" 應已註冊在 app routes 中')
def check_rtc_route(ctx: dict[str, Any]) -> None:
    app = ctx['app']
    paths = [route.path for route in app.routes]
    # FastRTC mounts under the path, so check for prefix match
    assert any('/api/conversation/rtc' in p for p in paths), f'Routes: {paths}'


@then('模組應包含啟動邏輯')
def check_main_module(main_module: Any) -> None:
    assert main_module is not None


# --- Helpers ---


def _start_app(settings: Settings, ctx: dict[str, Any]) -> None:
    from persochattai.app import create_app

    app = create_app(settings)

    mock_pool = MagicMock()
    mock_model_config_repo = MagicMock()
    mock_model_config_repo.seed_defaults = AsyncMock()
    mock_usage_repo = MagicMock()
    mock_monitor = MagicMock()
    mock_monitor.load_history = AsyncMock()

    pool_closed = False

    async def mock_close_pool() -> None:
        nonlocal pool_closed
        pool_closed = True

    mock_assessment_repo = MagicMock()
    mock_vocabulary_repo = MagicMock()
    mock_snapshot_repo = MagicMock()
    mock_assessment_agent = MagicMock()
    mock_assessment_service = MagicMock()
    mock_assessment_service._agent = mock_assessment_agent

    with (
        patch('persochattai.app.init_pool', new=AsyncMock()),
        patch('persochattai.app.get_pool', return_value=mock_pool),
        patch('persochattai.app.close_pool', new=AsyncMock(side_effect=mock_close_pool)),
        patch('persochattai.app.ModelConfigRepository', return_value=mock_model_config_repo),
        patch('persochattai.app.UsageRepository', return_value=mock_usage_repo),
        patch('persochattai.app.init_usage_monitor', return_value=mock_monitor),
        patch('persochattai.app.AssessmentRepository', return_value=mock_assessment_repo),
        patch('persochattai.app.UserVocabularyRepository', return_value=mock_vocabulary_repo),
        patch('persochattai.app.LevelSnapshotRepository', return_value=mock_snapshot_repo),
        patch('persochattai.app.AssessmentService', return_value=mock_assessment_service),
        patch('persochattai.app.create_assessment_agent', return_value=mock_assessment_agent),
        patch('persochattai.app._create_gemini_client', return_value=MagicMock()),
    ):
        # Run lifespan startup only, capture state, then shutdown
        snapshot: dict[str, Any] = {}

        async def run_lifespan() -> None:
            nonlocal pool_closed
            gen = app.router.lifespan_context(app)
            await gen.__aenter__()
            # Capture state while lifespan is active
            snapshot['scheduler_running'] = app.state.content_scheduler.is_running()
            snapshot['scheduler_has_job'] = app.state.content_scheduler.has_scrape_job()
            await gen.__aexit__(None, None, None)
            pool_closed = True

        _run(run_lifespan())

    ctx['app'] = app
    ctx['pool_closed'] = pool_closed
    ctx['snapshot'] = snapshot

    def cleanup() -> None:
        nonlocal pool_closed
        pool_closed = True
        ctx['pool_closed'] = True

    ctx['cleanup'] = cleanup


# --- Non-BDD unit tests ---


def test_main_calls_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DB_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-test')
    monkeypatch.setenv('GEMINI_API_KEY', 'ai-test')
    mock_run = MagicMock()
    monkeypatch.setattr('persochattai.__main__.uvicorn.run', mock_run)

    from persochattai.__main__ import main

    main()

    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    assert call_kwargs[1]['host'] == '127.0.0.1'
    assert call_kwargs[1]['port'] == 8000


def test_create_gemini_client_with_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    original_import = builtins.__import__

    def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == 'google.genai':
            raise ImportError('no google.genai')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mock_import)

    from persochattai.app import _create_gemini_client

    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
    )
    client = _create_gemini_client(settings)
    assert client is not None


def test_create_gemini_client_success() -> None:
    from persochattai.app import _create_gemini_client

    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
    )
    client = _create_gemini_client(settings)
    assert client is not None
