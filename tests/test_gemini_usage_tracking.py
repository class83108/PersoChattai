"""Gemini 音訊用量追蹤測試。"""

from __future__ import annotations

import asyncio
from datetime import UTC
from typing import Any

import pytest
from agent_core.usage_monitor import UsageMonitor
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/gemini_usage_tracking.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class _FakeUsage:
    def __init__(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0


# --- Fixtures ---


@pytest.fixture
def active_monitor() -> Any:
    """預設的 monitor，由 given step 透過 target_fixture 覆蓋。"""
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor()


@pytest.fixture
def record_result() -> dict[str, Any]:
    return {}


@pytest.fixture
def summary() -> dict[str, Any]:
    return {}


@pytest.fixture
def audio_record_obj() -> Any:
    return None


@pytest.fixture
def audio_dict() -> dict[str, Any]:
    return {}


@pytest.fixture
def gemini_cost() -> float:
    return 0.0


# --- Rule: ExtendedUsageMonitor 繼承 UsageMonitor ---


@given('一個 ExtendedUsageMonitor 實例', target_fixture='active_monitor')
def given_monitor() -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor()


@when(
    parsers.parse(
        '呼叫 record() 傳入含 {input_t:d} input_tokens 和 {output_t:d} output_tokens 的 usage'
    ),
    target_fixture='record_result',
)
def when_record_tokens(active_monitor: Any, input_t: int, output_t: int) -> dict[str, Any]:
    usage = _FakeUsage(input_tokens=input_t, output_tokens=output_t)
    result = active_monitor.record(usage)
    return {'record': result, 'monitor': active_monitor}


@then('records 新增一筆 UsageRecord')
def then_records_has_one(record_result: dict[str, Any]) -> None:
    assert len(record_result['monitor'].records) == 1


@then(parsers.parse('input_tokens 為 {input_t:d} 且 output_tokens 為 {output_t:d}'))
def then_tokens_match(record_result: dict[str, Any], input_t: int, output_t: int) -> None:
    rec = record_result['monitor'].records[-1]
    assert rec.input_tokens == input_t
    assert rec.output_tokens == output_t


@then('isinstance 檢查 UsageMonitor 為 True')
def then_isinstance_usage_monitor(active_monitor: Any) -> None:
    assert isinstance(active_monitor, UsageMonitor)


# --- Rule: 記錄 Gemini 音訊用量 ---


@given('一個停用的 ExtendedUsageMonitor 實例', target_fixture='active_monitor')
def given_disabled_monitor() -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor(enabled=False)


@when(
    parsers.parse(
        '呼叫 record_audio 帶入 duration_sec {dur} 和 direction "{direction}" 和 model "{model}"'
    ),
    target_fixture='record_result',
)
def when_record_audio(active_monitor: Any, dur: str, direction: str, model: str) -> dict[str, Any]:
    result = _run(
        active_monitor.record_audio(duration_sec=float(dur), direction=direction, model=model)
    )
    return {'result': result, 'monitor': active_monitor}


@then('audio_records 為空列表')
def then_audio_records_empty(record_result: dict[str, Any]) -> None:
    assert record_result['monitor'].audio_records == []


@then('record_audio 回傳 None')
def then_record_audio_returns_none(record_result: dict[str, Any]) -> None:
    assert record_result['result'] is None


@then('audio_records 新增一筆紀錄')
def then_audio_records_has_one(record_result: dict[str, Any]) -> None:
    assert len(record_result['monitor'].audio_records) == 1


@then(parsers.parse('audio_duration_sec 為 {dur} 且 direction 為 "{direction}"'))
def then_audio_fields_match(record_result: dict[str, Any], dur: str, direction: str) -> None:
    rec = record_result['monitor'].audio_records[-1]
    assert rec.audio_duration_sec == float(dur)
    assert rec.direction == direction


# --- Rule: GeminiAudioRecord 資料結構 ---


@given(
    parsers.parse(
        '一筆 GeminiAudioRecord 紀錄 duration {dur} direction "{direction}" model "{model}"'
    ),
    target_fixture='audio_record_obj',
)
def given_audio_record(dur: str, direction: str, model: str) -> Any:
    from datetime import datetime

    from persochattai.usage.schemas import GeminiAudioRecord

    return GeminiAudioRecord(
        timestamp=datetime.now(tz=UTC),
        audio_duration_sec=float(dur),
        direction=direction,
        model=model,
    )


@when('呼叫 to_dict()', target_fixture='audio_dict')
def when_to_dict(audio_record_obj: Any) -> dict[str, Any]:
    return audio_record_obj.to_dict()


@then(parsers.parse('回傳包含 "{k1}" 和 "{k2}" 和 "{k3}" 和 "{k4}"'))
def then_dict_has_keys(audio_dict: dict[str, Any], k1: str, k2: str, k3: str, k4: str) -> None:
    for k in (k1, k2, k3, k4):
        assert k in audio_dict


@then(parsers.parse('"{key}" 值為 {value}'))
def then_dict_value(audio_dict: dict[str, Any], key: str, value: str) -> None:
    assert audio_dict[key] == float(value)


# --- Rule: Gemini 音訊定價計算 ---


@given(parsers.parse('已記錄一筆 {model} input 音訊 {sec:d} 秒'))
def given_recorded_audio(active_monitor: Any, model: str, sec: int) -> None:
    _run(active_monitor.record_audio(duration_sec=float(sec), direction='input', model=model))


@when('計算 gemini 音訊總成本', target_fixture='gemini_cost')
def when_calculate_cost(active_monitor: Any) -> float:
    summary = active_monitor.get_summary()
    return summary['gemini_audio']['cost_usd']


@then(parsers.parse('成本等於 {sec:d} 秒的 token-based fallback 定價'))
def then_cost_fallback(gemini_cost: float, sec: int) -> None:
    from persochattai.usage.schemas import FALLBACK_GEMINI_PRICING

    tokens_per_sec = FALLBACK_GEMINI_PRICING['tokens_per_sec']
    audio_input = FALLBACK_GEMINI_PRICING['audio_input']
    expected = sec * tokens_per_sec * audio_input / 1_000_000
    assert gemini_cost == pytest.approx(expected)


# --- Rule: get_summary 包含 Gemini 成本 ---


@given(parsers.parse('已記錄 {n:d} 筆 token 紀錄'))
def given_token_records(active_monitor: Any, n: int) -> None:
    for _ in range(n):
        active_monitor.record(_FakeUsage(input_tokens=50, output_tokens=25))


@given(parsers.parse('已記錄 {n:d} 筆音訊紀錄'))
def given_audio_records(active_monitor: Any, n: int) -> None:
    for i in range(n):
        _run(
            active_monitor.record_audio(
                duration_sec=10.0 + i, direction='input', model='gemini-2.0-flash'
            )
        )


@when('呼叫 get_summary()', target_fixture='summary')
def when_get_summary(active_monitor: Any) -> dict[str, Any]:
    return active_monitor.get_summary()


@then(parsers.parse('summary 包含 "{key}" 區塊'))
def then_summary_has_block(summary: dict[str, Any], key: str) -> None:
    assert key in summary


@then(parsers.parse('gemini_audio 的 total_requests 為 {n:d}'))
def then_gemini_audio_total_requests(summary: dict[str, Any], n: int) -> None:
    assert summary['gemini_audio']['total_requests'] == n


@then(parsers.parse('total_requests 為 {n:d}'))
def then_total_requests(summary: dict[str, Any], n: int) -> None:
    assert summary['total_requests'] == n


@then(parsers.parse('回傳包含 "{key}" 欄位'))
def then_summary_has_key(summary: dict[str, Any], key: str) -> None:
    assert key in summary
