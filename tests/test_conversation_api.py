"""Conversation API 測試。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.app import create_app
from persochattai.config import Settings

scenarios('features/conversation_api.feature')

# Feature 用 "user-1" 等可讀名稱；path parameter 需要 UUID
_USER_MAP: dict[str, str] = {
    'user-1': 'a1111111-1111-1111-1111-111111111111',
    'user-no-history': 'b2222222-2222-2222-2222-222222222222',
}


def _resolve_user(name: str) -> str:
    return _USER_MAP.get(name, name)


# --- Fixtures ---


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock()
    states: dict[str, dict[str, Any]] = {}
    manager._states = states

    async def _start(user_id: str, source_type: str, source_ref: str) -> dict[str, Any]:
        conv_id = str(uuid.uuid4())
        states[conv_id] = {
            'conversation_id': conv_id,
            'status': 'preparing',
            'started_at': '2026-03-20T10:00:00',
            'user_id': user_id,
            'source_type': source_type,
        }
        return {'conversation_id': conv_id, 'status': 'preparing'}

    async def _get_state(conv_id: str) -> dict[str, Any] | None:
        return states.get(conv_id)

    async def _end(conv_id: str) -> dict[str, Any]:
        state = states.get(conv_id)
        if state:
            state['status'] = 'assessing'
        return {'conversation_id': conv_id, 'status': 'assessing'}

    async def _cancel(conv_id: str) -> dict[str, Any]:
        state = states.get(conv_id)
        if state:
            if state['status'] in ('completed', 'failed', 'cancelled'):
                msg = f'Cannot cancel conversation in {state["status"]} state'
                raise ValueError(msg)
            state['status'] = 'cancelled'
        return {'conversation_id': conv_id, 'status': 'cancelled'}

    manager.start_conversation = AsyncMock(side_effect=_start)
    manager.get_state = AsyncMock(side_effect=_get_state)
    manager.end_conversation = AsyncMock(side_effect=_end)
    manager.cancel_conversation = AsyncMock(side_effect=_cancel)
    manager.get_history = AsyncMock(return_value=[])
    manager.has_active_conversation = AsyncMock(return_value=False)
    return manager


@pytest.fixture
def client(mock_manager: MagicMock) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.conversation_manager = mock_manager
    return TestClient(app)


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Background ---


@given('測試用 ConversationManager 已初始化')
def manager_initialized() -> None:
    pass


# --- Given: 建立對話 ---


@given(parsers.parse('使用者 "{user_id}" 沒有進行中的對話'))
def user_no_active(user_id: str, mock_manager: MagicMock) -> None:
    mock_manager.has_active_conversation.return_value = False


@given(parsers.parse('使用者 "{user_id}" 已有一個 active 對話'))
def user_already_has_active(user_id: str, mock_manager: MagicMock, ctx: dict[str, Any]) -> None:
    ctx['conversation_id'] = str(uuid.uuid4())
    mock_manager.has_active_conversation.return_value = True


@given('ConversationManager 的 start_conversation 會拋出例外')
def manager_start_raises(mock_manager: MagicMock) -> None:
    mock_manager.start_conversation.side_effect = RuntimeError('internal error')


# --- Given: 查詢對話 ---


@given(parsers.parse('使用者 "{user_id}" 已建立一個對話'))
def user_created_conversation(user_id: str, mock_manager: MagicMock, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    mock_manager._states[conv_id] = {
        'conversation_id': conv_id,
        'status': 'preparing',
        'started_at': '2026-03-20T10:00:00',
        'user_id': user_id,
    }


# --- Given: 結束對話 ---


@given(parsers.parse('使用者 "{user_id}" 有一個 active 對話'))
def user_has_active(user_id: str, mock_manager: MagicMock, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    mock_manager._states[conv_id] = {
        'conversation_id': conv_id,
        'status': 'active',
        'started_at': '2026-03-20T10:00:00',
        'user_id': user_id,
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 completed 對話'))
def user_has_completed(user_id: str, mock_manager: MagicMock, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    mock_manager._states[conv_id] = {
        'conversation_id': conv_id,
        'status': 'completed',
    }


# --- Given: 對話歷史 ---


@given(parsers.parse('使用者 "{user_id}" 有 {count:d} 筆對話記錄'))
def user_has_n_conversations(user_id: str, count: int, mock_manager: MagicMock) -> None:
    mock_manager.get_history.return_value = [
        {
            'id': str(uuid.uuid4()),
            'status': 'completed',
            'started_at': f'2026-03-{20 - i:02d}T10:00:00',
            'ended_at': f'2026-03-{20 - i:02d}T10:15:00',
            'source_type': 'card',
        }
        for i in range(count)
    ]


# --- When: 建立對話 ---


@when(
    parsers.re(
        r'使用者 "(?P<user_id>[^"]+)" 以 source_type "(?P<source_type>[^"]*)" '
        r'和 source_ref "(?P<source_ref>[^"]*)" 建立對話'
    ),
    target_fixture='response',
)
def create_conversation(user_id: str, source_type: str, source_ref: str, client: TestClient) -> Any:
    return client.post(
        '/api/conversation/start',
        json={
            'user_id': _resolve_user(user_id),
            'source_type': source_type,
            'source_ref': source_ref,
        },
    )


@when('發送建立對話請求但缺少 user_id', target_fixture='response')
def create_conversation_missing_user_id(client: TestClient) -> Any:
    return client.post(
        '/api/conversation/start',
        json={'source_type': 'card', 'source_ref': 'card-abc'},
    )


# --- When: 查詢對話 ---


@when('查詢該對話的狀態', target_fixture='response')
def query_conversation(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.get(f'/api/conversation/{ctx["conversation_id"]}')


@when('以不存在的 conversation_id 查詢對話狀態', target_fixture='response')
def query_nonexistent(client: TestClient) -> Any:
    return client.get(f'/api/conversation/{uuid.uuid4()}')


@when(parsers.parse('以 "{value}" 查詢對話狀態'), target_fixture='response')
def query_invalid_id(value: str, client: TestClient) -> Any:
    return client.get(f'/api/conversation/{value}')


# --- When: 結束對話 ---


@when('結束該對話', target_fixture='response')
def end_conversation(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.post(f'/api/conversation/{ctx["conversation_id"]}/end')


@when('以不存在的 conversation_id 結束對話', target_fixture='response')
def end_nonexistent(client: TestClient) -> Any:
    return client.post(f'/api/conversation/{uuid.uuid4()}/end')


# --- When: 對話歷史 ---


@when(parsers.parse('查詢使用者 "{user_id}" 的對話歷史'), target_fixture='response')
def query_history(user_id: str, client: TestClient) -> Any:
    return client.get(f'/api/conversation/history/{_resolve_user(user_id)}')


@when(parsers.parse('以 "{value}" 查詢對話歷史'), target_fixture='response')
def query_history_invalid(value: str, client: TestClient) -> Any:
    return client.get(f'/api/conversation/history/{value}')


# --- When: 取消對話 ---


@when('取消該對話', target_fixture='response')
def cancel_conversation(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.post(f'/api/conversation/{ctx["conversation_id"]}/cancel')


@when('以不存在的 conversation_id 取消對話', target_fixture='response')
def cancel_nonexistent(client: TestClient) -> Any:
    return client.post(f'/api/conversation/{uuid.uuid4()}/cancel')


# --- When: 跨 endpoint ---


@when('以回應中的 conversation_id 查詢對話狀態', target_fixture='response')
def query_by_response_id(response: Any, client: TestClient, ctx: dict[str, Any]) -> Any:
    conv_id = response.json().get('conversation_id')
    ctx['conversation_id'] = conv_id
    return client.get(f'/api/conversation/{conv_id}')


# --- Then ---


@then(parsers.parse('回應狀態碼為 {status_code:d}'))
def check_status_code(response: Any, status_code: int) -> None:
    assert response.status_code == status_code


@then('回應包含 conversation_id')
def check_has_conversation_id(response: Any) -> None:
    assert 'conversation_id' in response.json()


@then(parsers.parse('回應包含 status 為 "{value}"'))
def check_status_value(response: Any, value: str) -> None:
    assert response.json()['status'] == value


@then('回應包含 status')
def check_has_status(response: Any) -> None:
    assert 'status' in response.json()


@then('回應包含 started_at')
def check_has_started_at(response: Any) -> None:
    assert 'started_at' in response.json()


@then(parsers.parse('回應包含 {count:d} 筆對話摘要'))
def check_count(response: Any, count: int) -> None:
    assert len(response.json()) == count


@then('每筆摘要包含 id、status、started_at、ended_at、source_type')
def check_summary_fields(response: Any) -> None:
    required = {'id', 'status', 'started_at', 'ended_at', 'source_type'}
    for item in response.json():
        assert required.issubset(item.keys())


@then('結果按 started_at 降序排列')
def check_descending(response: Any) -> None:
    timestamps = [item['started_at'] for item in response.json()]
    assert timestamps == sorted(timestamps, reverse=True)


@then('回應為空陣列')
def check_empty(response: Any) -> None:
    assert response.json() == []
