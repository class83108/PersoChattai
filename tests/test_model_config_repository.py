"""模型配置 Repository 測試。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/model_config_repository.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


def _make_mock_pool() -> tuple[AsyncMock, AsyncMock]:
    """建立支援 async with pool.acquire() as conn 的 mock。"""
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    conn.execute = AsyncMock()
    conn.fetchval = AsyncMock(return_value=0)

    @asynccontextmanager
    async def _transaction():  # type: ignore[no-untyped-def]
        yield

    conn.transaction = _transaction

    @asynccontextmanager
    async def _acquire():  # type: ignore[no-untyped-def]
        yield conn

    pool.acquire = _acquire
    return pool, conn


def _make_claude_model_row(
    model_id: str = 'claude-sonnet-4-20250514',
    display_name: str = 'Claude Sonnet 4',
    is_active: bool = True,
) -> dict[str, Any]:
    import json
    from datetime import UTC, datetime
    from uuid import uuid4

    return {
        'id': str(uuid4()),
        'provider': 'claude',
        'model_id': model_id,
        'display_name': display_name,
        'is_active': is_active,
        'pricing': json.dumps(
            {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30}
        ),
        'created_at': datetime.now(tz=UTC),
        'updated_at': datetime.now(tz=UTC),
    }


def _make_gemini_model_row(
    model_id: str = 'gemini-2.0-flash',
    display_name: str = 'Gemini 2.0 Flash',
    is_active: bool = True,
) -> dict[str, Any]:
    import json
    from datetime import UTC, datetime
    from uuid import uuid4

    return {
        'id': str(uuid4()),
        'provider': 'gemini',
        'model_id': model_id,
        'display_name': display_name,
        'is_active': is_active,
        'pricing': json.dumps(
            {'text_input': 0.10, 'audio_input': 0.70, 'output': 0.40, 'tokens_per_sec': 25}
        ),
        'created_at': datetime.now(tz=UTC),
        'updated_at': datetime.now(tz=UTC),
    }


def _default_model_rows() -> list[dict[str, Any]]:
    return [
        _make_claude_model_row('claude-sonnet-4-20250514', 'Claude Sonnet 4', is_active=True),
        _make_claude_model_row('claude-opus-4-20250514', 'Claude Opus 4', is_active=False),
        _make_claude_model_row('claude-haiku-4-20250514', 'Claude Haiku 4', is_active=False),
        _make_gemini_model_row('gemini-2.0-flash', 'Gemini 2.0 Flash', is_active=True),
        _make_gemini_model_row('gemini-2.5-flash', 'Gemini 2.5 Flash', is_active=False),
    ]


# --- Fixtures ---


@pytest.fixture
def mock_pool_and_conn() -> tuple[AsyncMock, AsyncMock]:
    return _make_mock_pool()


@pytest.fixture
def mock_pool(mock_pool_and_conn: tuple[AsyncMock, AsyncMock]) -> AsyncMock:
    return mock_pool_and_conn[0]


@pytest.fixture
def mock_conn(mock_pool_and_conn: tuple[AsyncMock, AsyncMock]) -> AsyncMock:
    return mock_pool_and_conn[1]


@pytest.fixture
def repo(mock_pool: AsyncMock) -> Any:
    from persochattai.usage.model_config_repository import ModelConfigRepository

    return ModelConfigRepository(mock_pool)


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Rule: 啟動時 seed 預設模型 ---


@given('一個空的 model_config table')
def given_empty_table(mock_conn: AsyncMock) -> None:
    mock_conn.fetchval = AsyncMock(return_value=0)


@when('執行 seed 邏輯', target_fixture='result')
def when_seed(repo: Any, mock_conn: AsyncMock) -> dict[str, Any]:
    _run(repo.seed_defaults())
    return {'conn': mock_conn}


@then(parsers.parse('DB 有 {n:d} 筆 Claude 模型（sonnet, opus, haiku）'))
def then_claude_models(result: dict[str, Any], n: int) -> None:
    conn = result['conn']
    calls = conn.fetchrow.call_args_list
    claude_inserts = [c for c in calls if 'claude' in str(c)]
    assert len(claude_inserts) == n


@then(parsers.parse('DB 有 {n:d} 筆 Gemini 模型（2.0-flash, 2.5-flash）'))
def then_gemini_models(result: dict[str, Any], n: int) -> None:
    conn = result['conn']
    calls = conn.fetchrow.call_args_list
    gemini_inserts = [c for c in calls if 'gemini' in str(c)]
    assert len(gemini_inserts) == n


@then('每個 provider 各有一個 is_active 為 TRUE 的模型')
def then_one_active_per_provider(result: dict[str, Any]) -> None:
    conn = result['conn']
    calls = conn.fetchrow.call_args_list
    active_calls = [c for c in calls if 'True' in str(c) or 'true' in str(c).lower()]
    # 至少 2 個 active（一個 claude、一個 gemini）
    assert len(active_calls) >= 2


@given(parsers.parse('model_config table 已有 {n:d} 筆 Claude 模型'))
def given_existing_models(mock_conn: AsyncMock, n: int) -> None:
    mock_conn.fetchval = AsyncMock(return_value=n)


@then(parsers.parse('DB 仍然只有 {n:d} 筆 Claude 模型'))
def then_no_extra_models(result: dict[str, Any], n: int) -> None:
    conn = result['conn']
    # seed 不應新增任何 INSERT
    assert conn.fetchrow.call_count == 0


# --- Rule: CRUD 正常操作 ---


@given('DB 有預設的 5 筆模型配置')
def given_default_models(mock_conn: AsyncMock) -> None:
    mock_conn.fetch = AsyncMock(return_value=_default_model_rows())
    mock_conn.fetchval = AsyncMock(return_value=5)


@when('呼叫 list_models()', target_fixture='result')
def when_list_models(repo: Any) -> dict[str, Any]:
    models = _run(repo.list_models())
    return {'models': models}


@then(parsers.parse('回傳 {n:d} 筆 ModelConfig'))
def then_n_models(result: dict[str, Any], n: int) -> None:
    assert len(result['models']) == n


@when(parsers.parse('呼叫 list_models(provider="{provider}")'), target_fixture='result')
def when_list_models_by_provider(repo: Any, mock_conn: AsyncMock, provider: str) -> dict[str, Any]:
    filtered = [r for r in _default_model_rows() if r['provider'] == provider]
    mock_conn.fetch = AsyncMock(return_value=filtered)
    models = _run(repo.list_models(provider=provider))
    return {'models': models}


@then(parsers.parse('每筆的 provider 都是 "{provider}"'))
def then_all_provider(result: dict[str, Any], provider: str) -> None:
    for m in result['models']:
        assert m.provider == provider


@when(parsers.parse('呼叫 get_active_model(provider="{provider}")'), target_fixture='result')
def when_get_active(repo: Any, mock_conn: AsyncMock, provider: str) -> dict[str, Any]:
    active_row = next(
        r for r in _default_model_rows() if r['provider'] == provider and r['is_active']
    )
    mock_conn.fetchrow = AsyncMock(return_value=active_row)
    model = _run(repo.get_active_model(provider=provider))
    return {'model': model}


@then('回傳 is_active 為 TRUE 的 Claude 模型')
def then_active_claude(result: dict[str, Any]) -> None:
    assert result['model'].is_active is True
    assert result['model'].provider == 'claude'


@when('呼叫 create_model 帶入一筆新的 Gemini 模型', target_fixture='result')
def when_create_model(repo: Any, mock_conn: AsyncMock) -> dict[str, Any]:
    from persochattai.usage.schemas import ModelConfig

    new_model = ModelConfig(
        provider='gemini',
        model_id='gemini-2.5-pro',
        display_name='Gemini 2.5 Pro',
        is_active=False,
        pricing={'text_input': 1.25, 'audio_input': 2.50, 'output': 5.00, 'tokens_per_sec': 25},
    )
    row = _make_gemini_model_row('gemini-2.5-pro', 'Gemini 2.5 Pro', is_active=False)
    mock_conn.fetchrow = AsyncMock(return_value=row)
    created = _run(repo.create_model(new_model))
    return {'model': created, 'conn': mock_conn}


@then('DB 多一筆模型紀錄')
def then_model_inserted(result: dict[str, Any]) -> None:
    conn = result['conn']
    conn.fetchrow.assert_called_once()
    sql = conn.fetchrow.call_args[0][0]
    assert 'INSERT' in sql.upper()


@then('回傳的 ModelConfig 包含完整欄位')
def then_model_complete(result: dict[str, Any]) -> None:
    from persochattai.usage.schemas import ModelConfig

    assert isinstance(result['model'], ModelConfig)
    assert result['model'].model_id == 'gemini-2.5-pro'


@when(parsers.parse('呼叫 update_model 更新 "{model_id}" 的 pricing'), target_fixture='result')
def when_update_model(repo: Any, mock_conn: AsyncMock, model_id: str) -> dict[str, Any]:
    import json
    from datetime import UTC, datetime

    new_pricing = {'text_input': 0.20, 'audio_input': 1.00, 'output': 0.80, 'tokens_per_sec': 25}
    updated_row = _make_gemini_model_row(model_id)
    updated_row['pricing'] = json.dumps(new_pricing)
    updated_row['updated_at'] = datetime.now(tz=UTC)
    mock_conn.fetchrow = AsyncMock(return_value=updated_row)
    model = _run(repo.update_model(model_id, {'pricing': new_pricing}))
    return {'model': model, 'conn': mock_conn}


@then('DB 中該模型的 pricing 已更新')
def then_pricing_updated(result: dict[str, Any]) -> None:
    conn = result['conn']
    # fetchrow is called twice: SELECT (exists check) + UPDATE RETURNING
    calls = conn.fetchrow.call_args_list
    update_calls = [c for c in calls if 'UPDATE' in c[0][0].upper()]
    assert len(update_calls) == 1


@then('updated_at 時間已更新')
def then_updated_at(result: dict[str, Any]) -> None:
    assert result['model'].updated_at is not None


@given(parsers.parse('"{model_id}" 不是 active 模型'))
def given_not_active(mock_conn: AsyncMock, model_id: str) -> None:
    mock_conn.fetchrow = AsyncMock(return_value={'is_active': False, 'model_id': model_id})


@when(parsers.parse('呼叫 delete_model("{model_id}")'), target_fixture='result')
def when_delete_model(repo: Any, mock_conn: AsyncMock, model_id: str) -> dict[str, Any]:
    # mock_conn.fetchrow may already be set by given step (active or not active)
    # If not set by given, default to non-active
    current = mock_conn.fetchrow
    if not hasattr(current, '_mock_return_value') or current.return_value is None:
        mock_conn.fetchrow = AsyncMock(return_value={'is_active': False, 'model_id': model_id})
    mock_conn.execute = AsyncMock()
    try:
        _run(repo.delete_model(model_id))
        return {'conn': mock_conn}
    except Exception as e:
        return {'error': e}


@then(parsers.parse('DB 剩 {n:d} 筆模型'))
def then_model_deleted(result: dict[str, Any], n: int) -> None:
    conn = result['conn']
    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert 'DELETE' in sql.upper()


# --- Rule: 切換 active model ---


@given(parsers.parse('Claude 的 active model 是 "{model_id}"'))
def given_claude_active(mock_conn: AsyncMock, model_id: str) -> None:
    mock_conn.fetchrow = AsyncMock(return_value=_make_claude_model_row(model_id, is_active=True))


@when(
    parsers.parse('呼叫 set_active_model(provider="{provider}", model_id="{model_id}")'),
    target_fixture='result',
)
def when_set_active(
    repo: Any, mock_conn: AsyncMock, provider: str, model_id: str
) -> dict[str, Any]:
    # For nonexistent models, fetchrow returns None
    if 'nonexistent' in model_id or 'invalid' in model_id:
        mock_conn.fetchrow = AsyncMock(return_value=None)
    elif provider == 'claude':
        mock_conn.fetchrow = AsyncMock(
            return_value=_make_claude_model_row(model_id, is_active=False)
        )
    else:
        mock_conn.fetchrow = AsyncMock(
            return_value=_make_gemini_model_row(model_id, is_active=False)
        )
    mock_conn.execute = AsyncMock()
    try:
        _run(repo.set_active_model(provider=provider, model_id=model_id))
        return {'conn': mock_conn, 'provider': provider, 'model_id': model_id}
    except Exception as e:
        return {'error': e}


@then(parsers.parse('"{model_id}" 的 is_active 為 TRUE'))
def then_is_active_true(result: dict[str, Any], model_id: str) -> None:
    conn = result['conn']
    # Verify UPDATE calls were made
    assert conn.execute.call_count >= 1


@then(parsers.parse('"{model_id}" 的 is_active 為 FALSE'))
def then_is_active_false(result: dict[str, Any], model_id: str) -> None:
    # The set_active_model should deactivate old and activate new
    conn = result['conn']
    assert conn.execute.call_count >= 1


@then(parsers.parse('"{model_id}" 的 is_active 仍為 TRUE'))
def then_is_active_still_true(result: dict[str, Any], model_id: str) -> None:
    # Idempotent: still works without error
    assert result['model_id'] == model_id


# --- Rule: 錯誤處理 ---


@when(
    parsers.parse('呼叫 create_model 帶入已存在的 model_id "{model_id}"'),
    target_fixture='result',
)
def when_create_duplicate(repo: Any, mock_conn: AsyncMock, model_id: str) -> dict[str, Any]:
    import asyncpg

    from persochattai.usage.schemas import ModelConfig

    mock_conn.fetchrow = AsyncMock(side_effect=asyncpg.UniqueViolationError(''))
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
def given_is_active(mock_conn: AsyncMock, model_id: str) -> None:
    mock_conn.fetchrow = AsyncMock(return_value={'is_active': True, 'model_id': model_id})


@then('拋出 ActiveModelDeleteError')
def then_active_delete_error(result: dict[str, Any]) -> None:
    from persochattai.usage.model_config_repository import ActiveModelDeleteError

    assert isinstance(result['error'], ActiveModelDeleteError)


@when(parsers.parse('呼叫 update_model("{model_id}", ...)'), target_fixture='result')
def when_update_nonexistent(repo: Any, mock_conn: AsyncMock, model_id: str) -> dict[str, Any]:
    mock_conn.fetchrow = AsyncMock(return_value=None)
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
def when_query_pricing(repo: Any, mock_conn: AsyncMock, model_id: str) -> dict[str, Any]:
    rows = _default_model_rows()
    row = next(r for r in rows if r['model_id'] == model_id)
    mock_conn.fetchrow = AsyncMock(return_value=row)
    model = _run(repo.get_model(model_id))
    return {'pricing': model.pricing}


@then(parsers.parse('pricing 包含 "{k1}", "{k2}", "{k3}", "{k4}" 欄位'))
def then_pricing_fields(result: dict[str, Any], k1: str, k2: str, k3: str, k4: str) -> None:
    pricing = result['pricing']
    for k in (k1, k2, k3, k4):
        assert k in pricing
