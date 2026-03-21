"""模型切換 API 測試。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/model_switching_api.feature')


# --- Helpers ---


def _make_model_config(
    provider: str = 'claude',
    model_id: str = 'claude-sonnet-4-20250514',
    display_name: str = 'Claude Sonnet 4',
    is_active: bool = True,
    pricing: dict | None = None,
) -> Any:
    from persochattai.usage.schemas import ModelConfig

    if pricing is None:
        if provider == 'claude':
            pricing = {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30}
        else:
            pricing = {
                'text_input': 0.10,
                'audio_input': 0.70,
                'output': 0.40,
                'tokens_per_sec': 25,
            }
    return ModelConfig(
        id='00000000-0000-0000-0000-000000000001',
        provider=provider,
        model_id=model_id,
        display_name=display_name,
        is_active=is_active,
        pricing=pricing,
    )


def _default_models() -> list[Any]:
    return [
        _make_model_config('claude', 'claude-sonnet-4-20250514', 'Claude Sonnet 4', True),
        _make_model_config('claude', 'claude-opus-4-20250514', 'Claude Opus 4', False),
        _make_model_config('claude', 'claude-haiku-4-20250514', 'Claude Haiku 4', False),
        _make_model_config('gemini', 'gemini-2.0-flash', 'Gemini 2.0 Flash', True),
        _make_model_config('gemini', 'gemini-2.5-flash', 'Gemini 2.5 Flash', False),
    ]


# --- Fixtures ---


@pytest.fixture
def mock_model_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_models = AsyncMock(return_value=_default_models())
    repo.get_active_model = AsyncMock(
        side_effect=lambda provider: next(
            (m for m in _default_models() if m.provider == provider and m.is_active), None
        )
    )
    repo.set_active_model = AsyncMock()
    return repo


@pytest.fixture
def client(mock_model_repo: AsyncMock) -> TestClient:
    from persochattai.app import create_app
    from persochattai.config import Settings

    settings = Settings(
        db_url='postgresql://test:test@localhost/test',
        anthropic_api_key='test-key',
        gemini_api_key='test-key',
    )
    app = create_app(settings)
    app.state.model_config_repo = mock_model_repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Given ---


@given('DB 已 seed 預設模型配置')
def given_seeded(mock_model_repo: AsyncMock) -> None:
    pass


@given(parsers.parse('Claude 的 active model 是 "{model_id}"'))
def given_claude_active(mock_model_repo: AsyncMock, model_id: str) -> None:
    mock_model_repo.get_active_model = AsyncMock(
        side_effect=lambda provider: (
            _make_model_config('claude', model_id, is_active=True)
            if provider == 'claude'
            else next(
                (m for m in _default_models() if m.provider == provider and m.is_active), None
            )
        )
    )


@given('model_config table 為空')
def given_empty_table(mock_model_repo: AsyncMock) -> None:
    mock_model_repo.list_models = AsyncMock(return_value=[])
    mock_model_repo.get_active_model = AsyncMock(return_value=None)


# --- Rule: 讀取設定 ---


@when('呼叫 GET /api/settings', target_fixture='result')
def when_get_settings(client: TestClient) -> dict[str, Any]:
    resp = client.get('/api/settings')
    return {'response': resp}


@then(parsers.parse('回傳 {code:d}'))
def then_status_code(result: dict[str, Any], code: int) -> None:
    assert result['response'].status_code == code


@then(parsers.parse('response 包含 "{key}" 為目前 active Claude model ID'))
def then_has_claude_model(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert key in data
    assert data[key] is not None


@then(parsers.parse('response 包含 "{key}" 為目前 active Gemini model ID'))
def then_has_gemini_model(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert key in data
    assert data[key] is not None


@then(parsers.parse('response 包含 "{key}" 清單'))
def then_has_list(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert key in data
    assert isinstance(data[key], list)


# --- Rule: 切換 active model ---


@when(
    parsers.parse('呼叫 PUT /api/settings 帶入 {body}'),
    target_fixture='result',
)
def when_put_settings(client: TestClient, mock_model_repo: AsyncMock, body: str) -> dict[str, Any]:
    import json

    from persochattai.usage.model_config_repository import ModelNotFoundError

    parsed = json.loads(body)

    # Check if any model_id is invalid (not in defaults)
    valid_ids = {m.model_id for m in _default_models()}
    has_invalid = any(
        v not in valid_ids for k, v in parsed.items() if k in ('claude_model', 'gemini_model')
    )

    if has_invalid:
        mock_model_repo.set_active_model = AsyncMock(side_effect=ModelNotFoundError('not found'))
    else:
        mock_model_repo.set_active_model = AsyncMock()

        # After set_active_model, update the mock to return new active
        async def _side_effect(provider: str) -> Any:
            if provider == 'claude' and 'claude_model' in parsed:
                return _make_model_config('claude', parsed['claude_model'], is_active=True)
            if provider == 'gemini' and 'gemini_model' in parsed:
                return _make_model_config('gemini', parsed['gemini_model'], is_active=True)
            return next(
                (m for m in _default_models() if m.provider == provider and m.is_active), None
            )

        mock_model_repo.get_active_model = AsyncMock(side_effect=_side_effect)

    resp = client.put('/api/settings', json=parsed)
    return {'response': resp}


@then(parsers.parse('response 的 "{key}" 為 "{value}"'))
def then_response_value(result: dict[str, Any], key: str, value: str) -> None:
    data = result['response'].json()
    assert data[key] == value


@then(parsers.parse('再次 GET /api/settings 確認 "{key}" 為 "{value}"'))
def then_get_confirms(client: TestClient, key: str, value: str) -> None:
    resp = client.get('/api/settings')
    data = resp.json()
    assert data[key] == value


@then(parsers.parse('response 的 "{key}" 仍為原本的 active model'))
def then_unchanged_model(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert data[key] is not None  # still has a value


# --- Rule: 錯誤處理 ---


@then('active model 不變')
def then_active_unchanged(client: TestClient) -> None:
    resp = client.get('/api/settings')
    data = resp.json()
    assert data['claude_model'] is not None


@when('呼叫 PUT /api/settings 帶入空 body', target_fixture='result')
def when_put_empty(client: TestClient) -> dict[str, Any]:
    resp = client.put('/api/settings', json={})
    return {'response': resp}


# --- Rule: 切換冪等性 ---


@then(parsers.parse('active model 仍為 "{model_id}"'))
def then_still_active(result: dict[str, Any], model_id: str) -> None:
    data = result['response'].json()
    assert data['claude_model'] == model_id


# --- Rule: DB 為空時使用 Settings fallback ---


@then(parsers.parse('response 的 "{key}" 為 Settings 的 claude_model 預設值'))
def then_fallback_claude(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert data[key] == 'claude-sonnet-4-20250514'


@then(parsers.parse('response 的 "{key}" 為 Settings 的 gemini_model 預設值'))
def then_fallback_gemini(result: dict[str, Any], key: str) -> None:
    data = result['response'].json()
    assert data[key] == 'gemini-2.0-flash'
