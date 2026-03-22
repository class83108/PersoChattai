"""API 使用紀錄持久化測試。"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent_core.usage_monitor import UsageRecord
from pytest_bdd import given, parsers, scenarios, then, when

from tests.helpers import make_mock_session

scenarios('features/usage_persistence.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class _FakeUsage:
    def __init__(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0


def _make_usage_record(input_tokens: int = 50, output_tokens: int = 25) -> UsageRecord:
    return UsageRecord(
        timestamp=datetime.now(tz=UTC),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _make_audio_record(duration: float = 10.0, direction: str = 'input') -> Any:
    from persochattai.usage.schemas import GeminiAudioRecord

    return GeminiAudioRecord(
        timestamp=datetime.now(tz=UTC),
        audio_duration_sec=duration,
        direction=direction,
        model='gemini-2.0-flash',
    )


def _make_token_row(input_tokens: int = 50, output_tokens: int = 25) -> MagicMock:
    row = MagicMock()
    row.input_tokens = input_tokens
    row.output_tokens = output_tokens
    row.cache_creation_input_tokens = 0
    row.cache_read_input_tokens = 0
    row.created_at = datetime.now(tz=UTC)
    return row


def _make_audio_row(duration: float = 10.0, direction: str = 'input') -> MagicMock:
    row = MagicMock()
    row.audio_duration_sec = duration
    row.direction = direction
    row.model = 'gemini-2.0-flash'
    row.created_at = datetime.now(tz=UTC)
    return row


# --- Fixtures ---


@pytest.fixture
def mock_session() -> AsyncMock:
    return make_mock_session()


@pytest.fixture
def repo(mock_session: AsyncMock) -> Any:
    from persochattai.usage.repository import UsageRepository

    return UsageRepository(mock_session)


@pytest.fixture
def mock_repo() -> AsyncMock:
    r = AsyncMock()
    r.save_token_record = AsyncMock()
    r.save_audio_record = AsyncMock()
    r.load_token_records = AsyncMock(return_value=[])
    r.load_audio_records = AsyncMock(return_value=[])
    return r


@pytest.fixture
def active_monitor() -> Any:
    """預設 monitor，由 given step 透過 target_fixture 覆蓋。"""
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor()


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Rule: UsageRepository 寫入紀錄 ---


@given('一個 mock DB pool 的 UsageRepository')
def given_repo(repo: Any) -> None:
    pass


@when(
    parsers.parse('呼叫 save_token_record 帶入一筆 UsageRecord 和 model "{model}"'),
    target_fixture='result',
)
def when_save_token(repo: Any, mock_session: AsyncMock, model: str) -> dict[str, Any]:
    record = _make_usage_record(input_tokens=100, output_tokens=50)
    _run(repo.save_token_record(record, model=model))
    return {'session': mock_session, 'record': record}


@then(parsers.parse('DB 收到一筆 usage_type "{usage_type}" 的 INSERT'))
def then_db_insert(result: dict[str, Any], usage_type: str) -> None:
    session = result['session']
    session.add.assert_called_once()
    added_obj = session.add.call_args[0][0]
    assert added_obj.usage_type == usage_type


@then('包含正確的 input_tokens 和 output_tokens')
def then_correct_tokens(result: dict[str, Any]) -> None:
    added_obj = result['session'].add.call_args[0][0]
    assert added_obj.input_tokens == 100
    assert added_obj.output_tokens == 50


@when('呼叫 save_audio_record 帶入一筆 GeminiAudioRecord', target_fixture='result')
def when_save_audio(repo: Any, mock_session: AsyncMock) -> dict[str, Any]:
    record = _make_audio_record(duration=20.0, direction='output')
    _run(repo.save_audio_record(record))
    return {'session': mock_session, 'record': record}


@then('包含正確的 audio_duration_sec 和 direction')
def then_correct_audio(result: dict[str, Any]) -> None:
    added_obj = result['session'].add.call_args[0][0]
    assert added_obj.audio_duration_sec == 20.0
    assert added_obj.direction == 'output'


# --- Rule: UsageRepository 載入歷史紀錄 ---


@given(parsers.parse('DB 有 {n:d} 筆 token 紀錄'))
def given_db_token_records(mock_session: AsyncMock, n: int) -> None:
    rows = [_make_token_row(50 + i, 25) for i in range(n)]
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = rows
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)


@when(parsers.parse('呼叫 load_token_records(days={days:d})'), target_fixture='result')
def when_load_tokens(repo: Any, days: int) -> dict[str, Any]:
    records = _run(repo.load_token_records(days=days))
    return {'records': records}


@then(parsers.parse('回傳 {n:d} 筆 UsageRecord'))
def then_n_usage_records(result: dict[str, Any], n: int) -> None:
    assert len(result['records']) == n
    for r in result['records']:
        assert isinstance(r, UsageRecord)


@given(parsers.parse('DB 有 {n:d} 筆 audio 紀錄'))
def given_db_audio_records(mock_session: AsyncMock, n: int) -> None:
    rows = [_make_audio_row(10.0 + i, 'input') for i in range(n)]
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = rows
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)


@when(parsers.parse('呼叫 load_audio_records(days={days:d})'), target_fixture='result')
def when_load_audio(repo: Any, days: int) -> dict[str, Any]:
    records = _run(repo.load_audio_records(days=days))
    return {'records': records}


@then(parsers.parse('回傳 {n:d} 筆 GeminiAudioRecord'))
def then_n_audio_records(result: dict[str, Any], n: int) -> None:
    from persochattai.usage.schemas import GeminiAudioRecord

    assert len(result['records']) == n
    for r in result['records']:
        assert isinstance(r, GeminiAudioRecord)


@given('DB 無任何紀錄')
def given_db_empty(mock_session: AsyncMock) -> None:
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)


@then('回傳空列表')
def then_empty_list(result: dict[str, Any]) -> None:
    assert result['records'] == []


# --- Rule: UsageRepositoryProtocol ---


@given('一個 UsageRepository 實例')
def given_repo_instance(repo: Any) -> None:
    pass


@then('isinstance 檢查 UsageRepositoryProtocol 為 True')
def then_isinstance_protocol(repo: Any) -> None:
    from persochattai.usage.schemas import UsageRepositoryProtocol

    assert isinstance(repo, UsageRepositoryProtocol)


# --- Rule: record_audio 自動持久化 ---


@given('一個注入 mock repository 的 ExtendedUsageMonitor', target_fixture='active_monitor')
def given_monitor_with_repo(mock_repo: AsyncMock) -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor(repository=mock_repo)


@given('一個無 repository 的 ExtendedUsageMonitor', target_fixture='active_monitor')
def given_monitor_no_repo() -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor()


@when(
    parsers.parse(
        '呼叫 record_audio 帶入 duration_sec {dur} 和 direction "{direction}" 和 model "{model}"'
    ),
    target_fixture='result',
)
def when_record_audio(active_monitor: Any, dur: str, direction: str, model: str) -> dict[str, Any]:
    result = _run(
        active_monitor.record_audio(duration_sec=float(dur), direction=direction, model=model)
    )
    return {'result': result, 'monitor': active_monitor}


@then('audio_records 新增一筆紀錄')
def then_audio_one(result: dict[str, Any]) -> None:
    assert len(result['monitor'].audio_records) == 1


@then('repository 的 save_audio_record 被呼叫一次')
def then_save_audio_called(active_monitor: Any, mock_repo: AsyncMock) -> None:
    mock_repo.save_audio_record.assert_called_once()


# --- Rule: record_and_persist ---


@when(
    parsers.parse(
        '呼叫 record_and_persist 傳入含 {input_t:d} input_tokens 和 {output_t:d} output_tokens 的 usage'
    ),
    target_fixture='result',
)
def when_record_and_persist(active_monitor: Any, input_t: int, output_t: int) -> dict[str, Any]:
    usage = _FakeUsage(input_tokens=input_t, output_tokens=output_t)
    _run(active_monitor.record_and_persist(usage))
    return {'monitor': active_monitor}


@then('records 新增一筆 UsageRecord')
def then_records_one(result: dict[str, Any]) -> None:
    assert len(result['monitor'].records) == 1


@then('repository 的 save_token_record 被呼叫一次')
def then_save_token_called(active_monitor: Any, mock_repo: AsyncMock) -> None:
    mock_repo.save_token_record.assert_called_once()


# --- Rule: App 啟動載入歷史 ---


@given(parsers.parse('repository 回傳 {nt:d} 筆 token 歷史和 {na:d} 筆 audio 歷史'))
def given_repo_history(mock_repo: AsyncMock, nt: int, na: int) -> None:
    token_records = [_make_usage_record() for _ in range(nt)]
    audio_records = [_make_audio_record() for _ in range(na)]
    mock_repo.load_token_records = AsyncMock(return_value=token_records)
    mock_repo.load_audio_records = AsyncMock(return_value=audio_records)


@given('repository 回傳空歷史')
def given_repo_empty_history(mock_repo: AsyncMock) -> None:
    mock_repo.load_token_records = AsyncMock(return_value=[])
    mock_repo.load_audio_records = AsyncMock(return_value=[])


@when('呼叫 load_history()', target_fixture='result')
def when_load_history(active_monitor: Any) -> dict[str, Any]:
    _run(active_monitor.load_history())
    return {'monitor': active_monitor}


@then(parsers.parse('records 有 {n:d} 筆紀錄'))
def then_records_count(result: dict[str, Any], n: int) -> None:
    assert len(result['monitor'].records) == n


@then(parsers.parse('audio_records 有 {n:d} 筆紀錄'))
def then_audio_records_count(result: dict[str, Any], n: int) -> None:
    assert len(result['monitor'].audio_records) == n


@then('records 為空列表')
def then_records_empty(result: dict[str, Any]) -> None:
    assert result['monitor'].records == []


@then('audio_records 為空列表')
def then_audio_records_empty(result: dict[str, Any]) -> None:
    assert result['monitor'].audio_records == []
