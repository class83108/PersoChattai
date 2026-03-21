"""Gemini Token-based 定價計算測試。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/gemini_token_pricing.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


def _make_mock_model_config_repo(
    models: dict[str, dict[str, float]] | None = None,
) -> AsyncMock:
    """建立 mock ModelConfigRepository，回傳指定模型的定價。"""
    from persochattai.usage.schemas import ModelConfig

    repo = AsyncMock()

    if models is None:
        models = {}

    async def _get_model(model_id: str) -> Any:
        if model_id in models:
            return ModelConfig(
                provider='gemini',
                model_id=model_id,
                display_name=model_id,
                is_active=True,
                pricing=models[model_id],
            )
        return None

    repo.get_model = AsyncMock(side_effect=_get_model)
    return repo


# --- Fixtures ---


@pytest.fixture
def active_monitor() -> Any:
    """預設的 monitor，由 given step 透過 target_fixture 覆蓋。"""
    from persochattai.usage.monitor import ExtendedUsageMonitor

    return ExtendedUsageMonitor()


@pytest.fixture
def result() -> dict[str, Any]:
    return {}


# --- Rule: Token-based 成本計算 ---


@given(
    parsers.parse(
        '一個 ExtendedUsageMonitor 且 DB 有 {model} 定價（audio_input={audio_input}, tokens_per_sec={tps}）'
    ),
    target_fixture='active_monitor',
)
def given_monitor_with_pricing(model: str, audio_input: str, tps: str) -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    mock_repo = _make_mock_model_config_repo(
        {
            model: {
                'text_input': 0.10,
                'audio_input': float(audio_input),
                'output': 0.40,
                'tokens_per_sec': int(tps),
            }
        }
    )
    return ExtendedUsageMonitor(model_config_repo=mock_repo)


@when(
    parsers.parse('記錄一筆 {sec:d} 秒 input 音訊（model "{model}"）'),
    target_fixture='result',
)
def when_record_audio(active_monitor: Any, sec: int, model: str) -> dict[str, Any]:
    _run(active_monitor.record_audio(duration_sec=float(sec), direction='input', model=model))
    return {'monitor': active_monitor}


@then(parsers.parse('gemini_audio 成本為 {expected}'))
def then_audio_cost(result: dict[str, Any], expected: str) -> None:
    summary = result['monitor'].get_summary()
    assert summary['gemini_audio']['cost_usd'] == pytest.approx(float(expected))


# --- Rule: Fallback 定價 ---


@given(
    parsers.parse('一個 ExtendedUsageMonitor 且 DB 無 "{model}" 的定價'),
    target_fixture='active_monitor',
)
def given_monitor_no_pricing(model: str) -> Any:
    from persochattai.usage.monitor import ExtendedUsageMonitor

    mock_repo = _make_mock_model_config_repo({})  # empty — no models
    return ExtendedUsageMonitor(model_config_repo=mock_repo)


@then('gemini_audio 成本使用 fallback 定價計算')
def then_fallback_cost(result: dict[str, Any]) -> None:
    summary = result['monitor'].get_summary()
    cost = summary['gemini_audio']['cost_usd']
    # Fallback should still produce a non-negative cost
    assert cost >= 0


@then('產生一筆 warning log')
def then_warning_log(result: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        # Re-calculate to capture log
        result['monitor'].get_summary()
    assert any(
        'warning' in r.message.lower()
        or 'fallback' in r.message.lower()
        or 'not found' in r.message.lower()
        for r in caplog.records
    )


# --- Rule: get_summary 反映正確定價 ---


@then(parsers.parse('get_summary() 的 gemini_audio.cost_usd 為 {expected}'))
def then_summary_cost(result: dict[str, Any], expected: str) -> None:
    summary = result['monitor'].get_summary()
    assert summary['gemini_audio']['cost_usd'] == pytest.approx(float(expected))
