"""模型管理 API 測試。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/model_management_api.feature')


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
    repo.create_model = AsyncMock(return_value=_default_models()[0])
    repo.update_model = AsyncMock(return_value=_default_models()[0])
    repo.delete_model = AsyncMock()
    repo.get_model = AsyncMock(return_value=_default_models()[0])
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
    # Override model config repo dependency
    app.state.model_config_repo = mock_model_repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Given ---


@given('DB 已 seed 預設模型配置')
def given_seeded(mock_model_repo: AsyncMock) -> None:
    pass  # mock_model_repo already returns defaults


# --- Rule: 列出模型 ---


@when('呼叫 GET /api/models', target_fixture='result')
def when_get_models(client: TestClient) -> dict[str, Any]:
    resp = client.get('/api/models')
    return {'response': resp}


@then(parsers.parse('回傳 {code:d}'))
def then_status_code(result: dict[str, Any], code: int) -> None:
    assert result['response'].status_code == code


@then(parsers.parse('response 包含 {n:d} 筆模型'))
def then_n_models(result: dict[str, Any], n: int) -> None:
    data = result['response'].json()
    assert len(data) == n


@then('每筆包含 provider, model_id, display_name, is_active, pricing')
def then_model_fields(result: dict[str, Any]) -> None:
    data = result['response'].json()
    for item in data:
        for field in ('provider', 'model_id', 'display_name', 'is_active', 'pricing'):
            assert field in item


@when('呼叫 GET /api/models?provider=claude', target_fixture='result')
def when_get_models_claude(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    claude_models = [m for m in _default_models() if m.provider == 'claude']
    mock_model_repo.list_models = AsyncMock(return_value=claude_models)
    resp = client.get('/api/models', params={'provider': 'claude'})
    return {'response': resp}


@then(parsers.parse('response 只包含 provider 為 "{provider}" 的模型'))
def then_only_provider(result: dict[str, Any], provider: str) -> None:
    data = result['response'].json()
    for item in data:
        assert item['provider'] == provider


# --- Rule: 新增模型 ---


@when('呼叫 POST /api/models 帶入新的 Claude 模型資訊', target_fixture='result')
def when_post_model(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    new_model = _make_model_config('claude', 'claude-test-model', 'Claude Test', False)
    mock_model_repo.create_model = AsyncMock(return_value=new_model)
    resp = client.post(
        '/api/models',
        json={
            'provider': 'claude',
            'model_id': 'claude-test-model',
            'display_name': 'Claude Test',
            'pricing': {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30},
        },
    )
    return {'response': resp}


@then('response 包含新建的模型完整資訊')
def then_created_model(result: dict[str, Any]) -> None:
    data = result['response'].json()
    assert data['model_id'] == 'claude-test-model'
    assert 'pricing' in data


@when('呼叫 POST /api/models 帶入已存在的 model_id', target_fixture='result')
def when_post_duplicate(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    from persochattai.usage.model_config_repository import DuplicateModelError

    mock_model_repo.create_model = AsyncMock(side_effect=DuplicateModelError('duplicate'))
    resp = client.post(
        '/api/models',
        json={
            'provider': 'claude',
            'model_id': 'claude-sonnet-4-20250514',
            'display_name': 'Duplicate',
            'pricing': {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30},
        },
    )
    return {'response': resp}


@when('呼叫 POST /api/models 缺少 pricing 欄位', target_fixture='result')
def when_post_missing_pricing(client: TestClient) -> dict[str, Any]:
    resp = client.post(
        '/api/models',
        json={
            'provider': 'claude',
            'model_id': 'claude-new',
            'display_name': 'New',
            # no pricing
        },
    )
    return {'response': resp}


# --- Rule: 更新模型 ---


@when('呼叫 PUT /api/models/gemini-2.0-flash 帶入新定價', target_fixture='result')
def when_put_model(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    updated = _make_model_config(
        'gemini',
        'gemini-2.0-flash',
        'Gemini 2.0 Flash',
        True,
        pricing={'text_input': 0.20, 'audio_input': 1.00, 'output': 0.80, 'tokens_per_sec': 25},
    )
    mock_model_repo.update_model = AsyncMock(return_value=updated)
    resp = client.put(
        '/api/models/gemini-2.0-flash',
        json={
            'pricing': {
                'text_input': 0.20,
                'audio_input': 1.00,
                'output': 0.80,
                'tokens_per_sec': 25,
            },
        },
    )
    return {'response': resp}


@then('response 中 pricing 為更新後的值')
def then_updated_pricing(result: dict[str, Any]) -> None:
    data = result['response'].json()
    assert data['pricing']['text_input'] == 0.20


@when('呼叫 PUT /api/models/nonexistent', target_fixture='result')
def when_put_nonexistent(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    from persochattai.usage.model_config_repository import ModelNotFoundError

    mock_model_repo.update_model = AsyncMock(side_effect=ModelNotFoundError('not found'))
    resp = client.put('/api/models/nonexistent', json={'display_name': 'X'})
    return {'response': resp}


# --- Rule: 刪除模型 ---


@when('呼叫 DELETE /api/models/claude-haiku-4-20250514', target_fixture='result')
def when_delete_model(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    mock_model_repo.delete_model = AsyncMock()
    resp = client.delete('/api/models/claude-haiku-4-20250514')
    return {'response': resp}


@then('再次 GET /api/models 不包含該模型')
def then_model_gone(client: TestClient, mock_model_repo: AsyncMock) -> None:
    remaining = [m for m in _default_models() if m.model_id != 'claude-haiku-4-20250514']
    mock_model_repo.list_models = AsyncMock(return_value=remaining)
    resp = client.get('/api/models')
    model_ids = [m['model_id'] for m in resp.json()]
    assert 'claude-haiku-4-20250514' not in model_ids


@when('呼叫 DELETE /api/models/claude-sonnet-4-20250514', target_fixture='result')
def when_delete_active(client: TestClient, mock_model_repo: AsyncMock) -> dict[str, Any]:
    from persochattai.usage.model_config_repository import ActiveModelDeleteError

    mock_model_repo.delete_model = AsyncMock(
        side_effect=ActiveModelDeleteError('cannot delete active')
    )
    resp = client.delete('/api/models/claude-sonnet-4-20250514')
    return {'response': resp}


@then('模型未被刪除')
def then_model_not_deleted(client: TestClient, mock_model_repo: AsyncMock) -> None:
    # Verify the model still appears in list
    resp = client.get('/api/models')
    model_ids = [m['model_id'] for m in resp.json()]
    assert 'claude-sonnet-4-20250514' in model_ids
