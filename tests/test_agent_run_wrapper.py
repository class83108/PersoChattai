"""Agent Run Wrapper 測試。"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/agent_run_wrapper.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class FakeAgent:
    """模擬 BYOA Agent，可控制 stream_message 輸出。"""

    def __init__(self, events: list[str | dict[str, Any]]) -> None:
        self._events = events

    async def stream_message(
        self,
        content: str,
        attachments: Any = None,
        stream_id: str | None = None,
    ) -> Any:
        for event in self._events:
            yield event


# --- Fixtures ---


@pytest.fixture
def agent_result() -> dict[str, Any]:
    return {}


@pytest.fixture
def fake_agent() -> FakeAgent:
    return FakeAgent([])


# --- Given ---


@given(
    parsers.parse("一個 Agent 會輸出有效 JSON 字串 '{json_str}'"),
    target_fixture='fake_agent',
)
def given_agent_valid_json(json_str: str) -> FakeAgent:
    return FakeAgent([json_str])


@given(
    '一個 Agent 會輸出 code fence 包裝的 JSON',
    target_fixture='fake_agent',
)
def given_agent_code_fence(docstring: str) -> FakeAgent:
    return FakeAgent([docstring.strip()])


@given(
    parsers.parse('一個 Agent 會輸出純文字 "{text}"'),
    target_fixture='fake_agent',
)
def given_agent_plain_text(text: str) -> FakeAgent:
    return FakeAgent([text])


@given(
    '一個 Agent 不會產生任何輸出',
    target_fixture='fake_agent',
)
def given_agent_empty() -> FakeAgent:
    return FakeAgent([])


@given(
    parsers.parse("一個 Agent 會輸出混合的 stream 包含 AgentEvent 和文字 '{json_str}'"),
    target_fixture='fake_agent',
)
def given_agent_mixed_stream(json_str: str) -> FakeAgent:
    events: list[str | dict[str, Any]] = [
        {'type': 'tool_call', 'data': {'name': 'some_tool'}},
        json_str,
        {'type': 'tool_result', 'data': {'result': 'ok'}},
    ]
    return FakeAgent(events)


# --- When ---


@when(
    parsers.parse('呼叫 agent_run 並傳入訊息 "{message}"'),
    target_fixture='agent_result',
)
def when_call_agent_run(fake_agent: FakeAgent, message: str) -> dict[str, Any]:
    from persochattai.agent_run import agent_run

    return _run(agent_run(fake_agent, message))


# --- Then ---


@then(parsers.parse('回傳結果為 dict 且包含 key "{key}" 值為 "{value}"'))
def then_result_has_str_key(agent_result: dict[str, Any], key: str, value: str) -> None:
    assert isinstance(agent_result, dict)
    assert agent_result[key] == value


@then(parsers.parse('回傳結果包含 key "{key}" 值為 {value:d}'))
def then_result_has_int_key(agent_result: dict[str, Any], key: str, value: int) -> None:
    assert agent_result[key] == value


@then(parsers.parse('回傳結果包含 key "{key}" 值為 "{value}"'))
def then_result_has_key_value(agent_result: dict[str, Any], key: str, value: str) -> None:
    assert agent_result[key] == value


@then(parsers.parse('回傳結果的 "{key}" 為空字串'))
def then_result_has_empty_key(agent_result: dict[str, Any], key: str) -> None:
    assert agent_result[key] == ''
