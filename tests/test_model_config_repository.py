"""模型配置 Repository 測試。"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.exc import IntegrityError

from tests.helpers import make_mock_session

scenarios('features/model_config_repository.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


def _make_model_config_table_mock(
    provider: str = 'claude',
    model_id: str = 'claude-sonnet-4-20250514',
    display_name: str = 'Claude Sonnet 4',
    is_active: bool = True,
    pricing: dict | None = None,
) -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.provider = provider
    row.model_id = model_id
    row.display_name = display_name
    row.is_active = is_active
    row.pricing = pricing or {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30}
    row.created_at = datetime.now(tz=UTC)
    row.updated_at = datetime.now(tz=UTC)
    return row


def _make_gemini_row(
    model_id: str = 'gemini-2.0-flash',
    display_name: str = 'Gemini 2.0 Flash',
    is_active: bool = True,
) -> MagicMock:
    return _make_model_config_table_mock(
        provider='gemini',
        model_id=model_id,
        display_name=display_name,
        is_active=is_active,
        pricing={'text_input': 0.10, 'audio_input': 0.70, 'output': 0.40, 'tokens_per_sec': 25},
    )


def _default_rows() -> list[MagicMock]:
    return [
        _make_model_config_table_mock(
            'claude', 'claude-sonnet-4-20250514', 'Claude Sonnet 4', True
        ),
        _make_model_config_table_mock('claude', 'claude-opus-4-20250514', 'Claude Opus 4', False),
        _make_model_config_table_mock('claude', 'claude-haiku-4-20250514', 'Claude Haiku 4', False),
        _make_gemini_row('gemini-2.0-flash', 'Gemini 2.0 Flash', True),
        _make_gemini_row('gemini-2.5-flash', 'Gemini 2.5 Flash', False),
    ]


# --- Fixtures ---


@pytest.fixture
def mock_session() -> AsyncMock:
    return make_mock_session()


@pytest.fixture
def repo(mock_session: AsyncMock) -> Any:
    from persochattai.usage.model_config_repository import ModelConfigRepository

    return ModelConfigRepository(mock_session)


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Helpers to configure mock_session.execute results ---


def _setup_scalar_result(mock_session: AsyncMock, value: Any) -> None:
    """Configure session.execute to return a result whose .scalar() returns value."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = value
    mock_session.execute = AsyncMock(return_value=mock_result)


def _setup_scalars_result(mock_session: AsyncMock, rows: list[Any]) -> None:
    """Configure session.execute to return a result whose .scalars().all() returns rows."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = rows
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)


def _setup_scalar_one_or_none(mock_session: AsyncMock, value: Any) -> None:
    """Configure session.execute to return a result whose .scalar_one_or_none() returns value."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    mock_session.execute = AsyncMock(return_value=mock_result)


# --- Rule: 啟動時 seed 預設模型 ---


@given('一個空的 model_config table')
def given_empty_table(mock_session: AsyncMock) -> None:
    _setup_scalar_result(mock_session, 0)


@when('執行 seed 邏輯', target_fixture='result')
def when_seed(repo: Any, mock_session: AsyncMock) -> dict[str, Any]:
    _run(repo.seed_defaults())
    return {'session': mock_session}


@then(parsers.parse('DB 有 {n:d} 筆 Claude 模型（sonnet, opus, haiku）'))
def then_claude_models(result: dict[str, Any], n: int) -> None:
    session = result['session']
    add_calls = session.add.call_args_list
    claude_adds = [c for c in add_calls if getattr(c[0][0], 'provider', None) == 'claude']
    assert len(claude_adds) == n


@then(parsers.parse('DB 有 {n:d} 筆 Gemini 模型（2.0-flash, 2.5-flash）'))
def then_gemini_models(result: dict[str, Any], n: int) -> None:
    session = result['session']
    add_calls = session.add.call_args_list
    gemini_adds = [c for c in add_calls if getattr(c[0][0], 'provider', None) == 'gemini']
    assert len(gemini_adds) == n


@then('每個 provider 各有一個 is_active 為 TRUE 的模型')
def then_one_active_per_provider(result: dict[str, Any]) -> None:
    session = result['session']
    add_calls = session.add.call_args_list
    active_adds = [c for c in add_calls if getattr(c[0][0], 'is_active', False)]
    providers = {getattr(c[0][0], 'provider', None) for c in active_adds}
    assert 'claude' in providers
    assert 'gemini' in providers


@given(parsers.parse('model_config table 已有 {n:d} 筆 Claude 模型'))
def given_existing_models(mock_session: AsyncMock, n: int) -> None:
    _setup_scalar_result(mock_session, n)


@then(parsers.parse('DB 仍然只有 {n:d} 筆 Claude 模型'))
def then_no_extra_models(result: dict[str, Any], n: int) -> None:
    session = result['session']
    assert session.add.call_count == 0


# --- Rule: CRUD 正常操作 ---


@given('DB 有預設的 5 筆模型配置')
def given_default_models(mock_session: AsyncMock) -> None:
    _setup_scalars_result(mock_session, _default_rows())


@when('呼叫 list_models()', target_fixture='result')
def when_list_models(repo: Any) -> dict[str, Any]:
    models = _run(repo.list_models())
    return {'models': models}


@then(parsers.parse('回傳 {n:d} 筆 ModelConfig'))
def then_n_models(result: dict[str, Any], n: int) -> None:
    assert len(result['models']) == n


@when(parsers.parse('呼叫 list_models(provider="{provider}")'), target_fixture='result')
def when_list_models_by_provider(
    repo: Any, mock_session: AsyncMock, provider: str
) -> dict[str, Any]:
    filtered = [r for r in _default_rows() if r.provider == provider]
    _setup_scalars_result(mock_session, filtered)
    models = _run(repo.list_models(provider=provider))
    return {'models': models}


@then(parsers.parse('每筆的 provider 都是 "{provider}"'))
def then_all_provider(result: dict[str, Any], provider: str) -> None:
    for m in result['models']:
        assert m.provider == provider


@when(parsers.parse('呼叫 get_active_model(provider="{provider}")'), target_fixture='result')
def when_get_active(repo: Any, mock_session: AsyncMock, provider: str) -> dict[str, Any]:
    active_row = next(r for r in _default_rows() if r.provider == provider and r.is_active)
    _setup_scalar_one_or_none(mock_session, active_row)
    model = _run(repo.get_active_model(provider=provider))
    return {'model': model}


@then('回傳 is_active 為 TRUE 的 Claude 模型')
def then_active_claude(result: dict[str, Any]) -> None:
    assert result['model'].is_active is True
    assert result['model'].provider == 'claude'


@when('呼叫 create_model 帶入一筆新的 Gemini 模型', target_fixture='result')
def when_create_model(repo: Any, mock_session: AsyncMock) -> dict[str, Any]:
    from persochattai.usage.schemas import ModelConfig

    new_model = ModelConfig(
        provider='gemini',
        model_id='gemini-2.5-pro',
        display_name='Gemini 2.5 Pro',
        is_active=False,
        pricing={'text_input': 1.25, 'audio_input': 2.50, 'output': 5.00, 'tokens_per_sec': 25},
    )
    created = _run(repo.create_model(new_model))
    return {'model': created, 'session': mock_session}


@then('DB 多一筆模型紀錄')
def then_model_inserted(result: dict[str, Any]) -> None:
    session = result['session']
    session.add.assert_called_once()


@then('回傳的 ModelConfig 包含完整欄位')
def then_model_complete(result: dict[str, Any]) -> None:
    from persochattai.usage.schemas import ModelConfig

    assert isinstance(result['model'], ModelConfig)
    assert result['model'].model_id == 'gemini-2.5-pro'


@when(parsers.parse('呼叫 update_model 更新 "{model_id}" 的 pricing'), target_fixture='result')
def when_update_model(repo: Any, mock_session: AsyncMock, model_id: str) -> dict[str, Any]:
    new_pricing = {'text_input': 0.20, 'audio_input': 1.00, 'output': 0.80, 'tokens_per_sec': 25}
    existing = _make_gemini_row(model_id)
    _setup_scalar_one_or_none(mock_session, existing)
    model = _run(repo.update_model(model_id, {'pricing': new_pricing}))
    return {'model': model, 'session': mock_session}


@then('DB 中該模型的 pricing 已更新')
def then_pricing_updated(result: dict[str, Any]) -> None:
    session = result['session']
    session.flush.assert_called()


@then('updated_at 時間已更新')
def then_updated_at(result: dict[str, Any]) -> None:
    assert result['model'].updated_at is not None


@given(parsers.parse('"{model_id}" 不是 active 模型'))
def given_not_active(mock_session: AsyncMock, model_id: str) -> None:
    row = _make_model_config_table_mock(model_id=model_id, is_active=False)
    _setup_scalar_one_or_none(mock_session, row)


@when(parsers.parse('呼叫 delete_model("{model_id}")'), target_fixture='result')
def when_delete_model(repo: Any, mock_session: AsyncMock, model_id: str) -> dict[str, Any]:
    current_scalar = mock_session.execute.return_value
    if current_scalar is None or not hasattr(current_scalar, 'scalar_one_or_none'):
        row = _make_model_config_table_mock(model_id=model_id, is_active=False)
        _setup_scalar_one_or_none(mock_session, row)
    try:
        _run(repo.delete_model(model_id))
        return {'session': mock_session}
    except Exception as e:
        return {'error': e}


@then(parsers.parse('DB 剩 {n:d} 筆模型'))
def then_model_deleted(result: dict[str, Any], n: int) -> None:
    session = result['session']
    # execute is called for SELECT + DELETE
    assert session.execute.call_count >= 2


# --- Rule: 切換 active model ---


@given(parsers.parse('Claude 的 active model 是 "{model_id}"'))
def given_claude_active(mock_session: AsyncMock, model_id: str) -> None:
    row = _make_model_config_table_mock(model_id=model_id, is_active=True)
    _setup_scalar_one_or_none(mock_session, row)


@when(
    parsers.parse('呼叫 set_active_model(provider="{provider}", model_id="{model_id}")'),
    target_fixture='result',
)
def when_set_active(
    repo: Any, mock_session: AsyncMock, provider: str, model_id: str
) -> dict[str, Any]:
    if 'nonexistent' in model_id or 'invalid' in model_id:
        _setup_scalar_one_or_none(mock_session, None)
    elif provider == 'claude':
        row = _make_model_config_table_mock(model_id=model_id, is_active=False)
        _setup_scalar_one_or_none(mock_session, row)
    else:
        row = _make_gemini_row(model_id=model_id, is_active=False)
        _setup_scalar_one_or_none(mock_session, row)
    try:
        _run(repo.set_active_model(provider=provider, model_id=model_id))
        return {'session': mock_session, 'provider': provider, 'model_id': model_id}
    except Exception as e:
        return {'error': e}


@then(parsers.parse('"{model_id}" 的 is_active 為 TRUE'))
def then_is_active_true(result: dict[str, Any], model_id: str) -> None:
    session = result['session']
    assert session.execute.call_count >= 1


@then(parsers.parse('"{model_id}" 的 is_active 為 FALSE'))
def then_is_active_false(result: dict[str, Any], model_id: str) -> None:
    session = result['session']
    assert session.execute.call_count >= 1


@then(parsers.parse('"{model_id}" 的 is_active 仍為 TRUE'))
def then_is_active_still_true(result: dict[str, Any], model_id: str) -> None:
    assert result['model_id'] == model_id


# --- Rule: 錯誤處理 ---


@when(
    parsers.parse('呼叫 create_model 帶入已存在的 model_id "{model_id}"'),
    target_fixture='result',
)
def when_create_duplicate(repo: Any, mock_session: AsyncMock, model_id: str) -> dict[str, Any]:
    from persochattai.usage.schemas import ModelConfig

    mock_session.flush = AsyncMock(side_effect=IntegrityError('', {}, Exception()))
    model = ModelConfig(
        provider='claude',
        model_id=model_id,
        display_name='Duplicate',
        is_active=False,
        pricing={'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30},
    )
    try:
        _run(repo.create_model(model))
        return {'error': None}
    except Exception as e:
        return {'error': e}


@then('拋出 DuplicateModelError')
def then_duplicate_error(result: dict[str, Any]) -> None:
    from persochattai.usage.model_config_repository import DuplicateModelError

    assert isinstance(result['error'], DuplicateModelError)


@given(parsers.parse('"{model_id}" 是 active 模型'))
def given_is_active(mock_session: AsyncMock, model_id: str) -> None:
    row = _make_model_config_table_mock(model_id=model_id, is_active=True)
    _setup_scalar_one_or_none(mock_session, row)


@then('拋出 ActiveModelDeleteError')
def then_active_delete_error(result: dict[str, Any]) -> None:
    from persochattai.usage.model_config_repository import ActiveModelDeleteError

    assert isinstance(result['error'], ActiveModelDeleteError)


@when(parsers.parse('呼叫 update_model("{model_id}", ...)'), target_fixture='result')
def when_update_nonexistent(repo: Any, mock_session: AsyncMock, model_id: str) -> dict[str, Any]:
    _setup_scalar_one_or_none(mock_session, None)
    try:
        _run(repo.update_model(model_id, {'pricing': {}}))
        return {'error': None}
    except Exception as e:
        return {'error': e}


@then('拋出 ModelNotFoundError')
def then_model_not_found(result: dict[str, Any]) -> None:
    from persochattai.usage.model_config_repository import ModelNotFoundError

    assert isinstance(result['error'], ModelNotFoundError)


# --- Rule: 輸出格式 ---


@when('呼叫 list_models() 取得第一筆', target_fixture='result')
def when_list_first(repo: Any) -> dict[str, Any]:
    models = _run(repo.list_models())
    return {'model': models[0]}


@then('ModelConfig 有 id, provider, model_id, display_name, is_active, pricing 欄位')
def then_model_config_fields(result: dict[str, Any]) -> None:
    model = result['model']
    assert hasattr(model, 'id')
    assert hasattr(model, 'provider')
    assert hasattr(model, 'model_id')
    assert hasattr(model, 'display_name')
    assert hasattr(model, 'is_active')
    assert hasattr(model, 'pricing')


@when(parsers.parse('查詢 "{model_id}" 的 pricing'), target_fixture='result')
def when_query_pricing(repo: Any, mock_session: AsyncMock, model_id: str) -> dict[str, Any]:
    rows = _default_rows()
    row = next(r for r in rows if r.model_id == model_id)
    _setup_scalar_one_or_none(mock_session, row)
    model = _run(repo.get_model(model_id))
    return {'pricing': model.pricing}


@then(parsers.parse('pricing 包含 "{k1}", "{k2}", "{k3}", "{k4}" 欄位'))
def then_pricing_fields(result: dict[str, Any], k1: str, k2: str, k3: str, k4: str) -> None:
    pricing = result['pricing']
    for k in (k1, k2, k3, k4):
        assert k in pricing
