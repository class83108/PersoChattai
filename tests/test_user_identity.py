"""使用者識別 API 測試。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.app import create_app
from persochattai.config import Settings

scenarios('features/user_identity.feature')


# --- Fixtures ---


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    repo = AsyncMock()
    repo._store: dict[str, dict[str, Any]] = {}

    async def _create(display_name: str) -> dict[str, Any]:
        # Check if already exists
        for user in repo._store.values():
            if user['display_name'] == display_name:
                return user
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'display_name': display_name,
            'current_level': None,
        }
        repo._store[user_id] = user
        return user

    async def _get_by_id(user_id: str) -> dict[str, Any] | None:
        return repo._store.get(user_id)

    async def _get_by_display_name(display_name: str) -> dict[str, Any] | None:
        for user in repo._store.values():
            if user['display_name'] == display_name:
                return user
        return None

    repo.create = AsyncMock(side_effect=_create)
    repo.get_by_id = AsyncMock(side_effect=_get_by_id)
    repo.get_by_display_name = AsyncMock(side_effect=_get_by_display_name)
    return repo


@pytest.fixture
def client(mock_user_repo: AsyncMock) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.user_repository = mock_user_repo
    return TestClient(app)


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Background ---


@given('測試用資料庫已初始化')
def db_initialized() -> None:
    pass


# --- Given ---


@given(parsers.parse('已存在暱稱為 "{name}" 的使用者'))
def existing_user(name: str, mock_user_repo: AsyncMock, ctx: dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    user = {
        'id': user_id,
        'display_name': name,
        'current_level': None,
    }
    mock_user_repo._store[user_id] = user
    ctx['existing_user_id'] = user_id


# --- When: POST /api/users ---


@when(parsers.parse('發送 POST /api/users，display_name 為 "{name}"'), target_fixture='response')
def post_user(name: str, client: TestClient) -> Any:
    return client.post('/api/users', json={'display_name': name})


@when('發送 POST /api/users，display_name 為空字串', target_fixture='response')
def post_user_empty(client: TestClient) -> Any:
    return client.post('/api/users', json={'display_name': ''})


@when(
    parsers.parse('發送 POST /api/users，display_name 為 {length:d} 個字的字串'),
    target_fixture='response',
)
def post_user_n_chars(length: int, client: TestClient) -> Any:
    name = 'A' * length
    return client.post('/api/users', json={'display_name': name})


@when(
    parsers.parse('發送 POST /api/users，display_name 為 "{name}" 兩次'), target_fixture='response'
)
def post_user_twice(name: str, client: TestClient, ctx: dict[str, Any]) -> Any:
    resp1 = client.post('/api/users', json={'display_name': name})
    resp2 = client.post('/api/users', json={'display_name': name})
    ctx['first_response'] = resp1
    ctx['second_response'] = resp2
    return resp2


# --- When: GET /api/users/{user_id} ---


@when('以該使用者的 id 發送 GET /api/users/{user_id}', target_fixture='response')
def get_user_by_ctx_id(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.get(f'/api/users/{ctx["existing_user_id"]}')


@when('以不存在的 UUID 發送 GET /api/users/{user_id}', target_fixture='response')
def get_user_nonexistent(client: TestClient) -> Any:
    return client.get(f'/api/users/{uuid.uuid4()}')


@when(parsers.parse('以 "{value}" 發送 GET /api/users/{{user_id}}'), target_fixture='response')
def get_user_invalid(value: str, client: TestClient) -> Any:
    return client.get(f'/api/users/{value}')


# --- Then ---


@then(parsers.parse('回應狀態碼為 {status_code:d}'))
def check_status_code(response: Any, status_code: int) -> None:
    assert response.status_code == status_code


@then(parsers.parse('回應包含 id 為合法 UUID'))
def check_valid_uuid(response: Any) -> None:
    data = response.json()
    uuid.UUID(data['id'])  # raises if invalid


@then(parsers.parse('回應包含 display_name 為 "{name}"'))
def check_display_name(response: Any, name: str) -> None:
    assert response.json()['display_name'] == name


@then('回應包含的 id 與既有使用者相同')
def check_same_id(response: Any, ctx: dict[str, Any]) -> None:
    assert response.json()['id'] == ctx['existing_user_id']


@then('兩次回應的 id 相同')
def check_both_ids_same(ctx: dict[str, Any]) -> None:
    id1 = ctx['first_response'].json()['id']
    id2 = ctx['second_response'].json()['id']
    assert id1 == id2


@then(parsers.parse('資料庫中 display_name 為 "{name}" 的 user 僅有一筆'))
def check_single_row(name: str, mock_user_repo: AsyncMock) -> None:
    count = sum(1 for u in mock_user_repo._store.values() if u['display_name'] == name)
    assert count == 1


@then('回應包含 id')
def check_has_id(response: Any) -> None:
    assert 'id' in response.json()


@then('回應包含 current_level')
def check_has_current_level(response: Any) -> None:
    assert 'current_level' in response.json()


@then('回應 JSON 僅包含 id 和 display_name 欄位')
def check_post_contract(response: Any) -> None:
    keys = set(response.json().keys())
    assert keys == {'id', 'display_name'}


@then('回應 JSON 包含 id、display_name、current_level 欄位')
def check_get_contract(response: Any) -> None:
    keys = set(response.json().keys())
    assert {'id', 'display_name', 'current_level'}.issubset(keys)
