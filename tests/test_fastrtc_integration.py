"""FastRTC 整合測試。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/fastrtc_integration.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('persochattai.conversation.manager._TRANSCRIPT_RETRY_DELAYS', [0, 0])


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.update_status = AsyncMock()
    repo.save_transcript = AsyncMock()
    repo.update_ended_at = AsyncMock()
    repo.list_by_user = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_scenario_designer() -> AsyncMock:
    designer = AsyncMock()
    designer.return_value = 'You are a hotel receptionist'
    return designer


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    client = MagicMock()
    session = AsyncMock()
    connect_cm = AsyncMock()
    connect_cm.__aenter__ = AsyncMock(return_value=session)
    connect_cm.__aexit__ = AsyncMock(return_value=False)
    client.aio.live.connect = MagicMock(return_value=connect_cm)
    return client


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Given: Stream 掛載 ---


@given('FastAPI app 已建立且 Stream 已掛載')
def app_with_stream(ctx: dict[str, Any]) -> None:
    from persochattai.conversation.stream import create_conversation_stream

    ctx['app'], ctx['stream'] = create_conversation_stream()


@given('ConversationManager 已初始化且 Stream 已掛載')
def manager_with_stream(
    mock_repo: MagicMock,
    mock_scenario_designer: AsyncMock,
    mock_gemini_client: MagicMock,
    ctx: dict[str, Any],
) -> None:
    from persochattai.conversation.manager import ConversationManager

    manager = ConversationManager(
        repository=mock_repo,
        scenario_designer=mock_scenario_designer,
        gemini_client=mock_gemini_client,
    )
    ctx['manager'] = manager


@given('ConversationManager 已初始化且有一個 active 對話')
def manager_with_active_conversation(
    mock_repo: MagicMock,
    mock_scenario_designer: AsyncMock,
    mock_gemini_client: MagicMock,
    ctx: dict[str, Any],
) -> None:
    from persochattai.conversation.manager import ConversationManager

    manager = ConversationManager(
        repository=mock_repo,
        scenario_designer=mock_scenario_designer,
        gemini_client=mock_gemini_client,
    )
    conv_id = str(uuid.uuid4())
    ctx['manager'] = manager
    ctx['conversation_id'] = conv_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': 'user-1',
        'status': 'active',
        'transcript': [],
    }


# --- When ---


@when(parsers.parse('使用者啟動對話且 scenario_designer 回傳 "{instruction}"'))
def start_conversation_with_instruction(
    instruction: str,
    mock_scenario_designer: AsyncMock,
    mock_gemini_client: MagicMock,
    ctx: dict[str, Any],
) -> None:
    mock_scenario_designer.return_value = instruction

    # Mock gemini connect to capture the handler config
    session = AsyncMock()

    async def _fake_stream(**kwargs: Any) -> Any:
        await asyncio.sleep(0)
        return
        yield

    session.start_stream = MagicMock(side_effect=_fake_stream)
    connect_cm = AsyncMock()
    connect_cm.__aenter__ = AsyncMock(return_value=session)
    connect_cm.__aexit__ = AsyncMock(return_value=False)
    mock_gemini_client.aio.live.connect = MagicMock(return_value=connect_cm)

    result = _run(ctx['manager'].start_conversation('user-1', 'card', 'card-abc'))
    ctx['conversation_id'] = result['conversation_id']


@when('handler 的 on_disconnect 被觸發')
def trigger_on_disconnect(ctx: dict[str, Any]) -> None:
    manager = ctx['manager']
    conv_id = ctx['conversation_id']
    _run(manager.handle_disconnection(conv_id))


# --- Then: Stream 掛載 ---


@then('app 應包含 /api/conversation/rtc/webrtc/offer 路由')
def check_rtc_route(ctx: dict[str, Any]) -> None:
    app = ctx['app']
    routes = [route.path for route in app.routes]
    assert any('/api/conversation/rtc/webrtc/offer' in r for r in routes)


# --- Then: Manager-Handler wiring ---


@then(parsers.parse('handler 的 system_instruction 應為 "{instruction}"'))
def check_handler_instruction(instruction: str, mock_gemini_client: MagicMock) -> None:
    call_kwargs = mock_gemini_client.aio.live.connect.call_args.kwargs
    config = call_kwargs.get('config')
    assert config is not None
    si = (
        config.system_instruction
        if hasattr(config, 'system_instruction')
        else config.get('system_instruction')
    )
    assert instruction in str(si)


@then('handler 的 gemini_client 應已設定')
def check_handler_has_client(mock_gemini_client: MagicMock) -> None:
    mock_gemini_client.aio.live.connect.assert_called_once()


@then('對話狀態應轉為 failed')
def check_state_failed(ctx: dict[str, Any]) -> None:
    manager = ctx['manager']
    conv_id = ctx['conversation_id']
    state = manager.get_state(conv_id)
    assert state['status'] == 'failed'
