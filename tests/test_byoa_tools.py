"""BYOA Tools 測試。"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/byoa_tools.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


def _make_card(title: str, difficulty_level: str, source_type: str, tags: str) -> dict[str, Any]:
    return {
        'id': str(uuid.uuid4()),
        'title': title,
        'difficulty_level': difficulty_level,
        'source_type': source_type,
        'tags': [t.strip() for t in tags.split(',')],
        'summary': f'Summary of {title}',
        'keywords': [],
        'source_url': None,
        'dialogue_snippets': None,
    }


# --- Fixtures ---


@pytest.fixture
def card_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.create = AsyncMock(side_effect=lambda data: {**data, 'id': str(uuid.uuid4())})
    repo.list_cards = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def assessment_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_user_history = AsyncMock(
        return_value={
            'snapshot': None,
            'recent_assessments': [],
            'vocabulary_stats': {'total_words': 0, 'recent_words': []},
        }
    )
    return svc


@pytest.fixture
def tool_result() -> dict[str, Any]:
    return {}


@pytest.fixture
def tool_list() -> list[str]:
    return []


@pytest.fixture
def cards_in_db() -> list[dict[str, Any]]:
    return []


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


# --- Given: query_cards ---


@given('資料庫有以下卡片', target_fixture='cards_in_db')
def given_cards_in_db(datatable: list[list[str]], card_repo: AsyncMock) -> list[dict[str, Any]]:
    headers = datatable[0]
    cards = [_make_card(**dict(zip(headers, row, strict=True))) for row in datatable[1:]]

    def _list_cards(
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        result = cards
        if source_type:
            result = [c for c in result if c['source_type'] == source_type]
        if difficulty:
            result = [c for c in result if c['difficulty_level'] == difficulty]
        if tag:
            result = [c for c in result if tag in c['tags']]
        return result[:limit]

    card_repo.list_cards = AsyncMock(side_effect=_list_cards)
    return cards


# --- Given: create_card ---


@given('一個可寫入的卡片 repository')
def given_writable_repo(card_repo: AsyncMock) -> None:
    pass


# --- Given: get_user_history ---


@given('使用者有 3 次評估紀錄和詞彙資料', target_fixture='assessment_service')
def given_user_with_history(user_id: str) -> AsyncMock:
    svc = AsyncMock()
    svc.get_user_history = AsyncMock(
        return_value={
            'snapshot': {'cefr_level': 'B1', 'avg_mtld': 55.0},
            'recent_assessments': [
                {'id': str(uuid.uuid4()), 'cefr_level': 'B1'},
                {'id': str(uuid.uuid4()), 'cefr_level': 'B1'},
                {'id': str(uuid.uuid4()), 'cefr_level': 'B2'},
            ],
            'vocabulary_stats': {'total_words': 120, 'recent_words': ['pragmatic']},
        }
    )
    return svc


@given('使用者無任何評估紀錄')
def given_user_no_history(assessment_service: AsyncMock) -> None:
    pass


# --- Given: tool registry ---


@given('已組裝的 tool registries')
def given_tool_registries() -> None:
    pass


# --- When: query_cards ---


@when(
    parsers.parse('呼叫 query_cards tool 帶入 difficulty_level "{level}"'),
    target_fixture='tool_result',
)
def when_query_cards_by_level(card_repo: AsyncMock, level: str) -> Any:
    from persochattai.tools import create_query_cards_handler

    handler = create_query_cards_handler(card_repo)
    return _run(handler(difficulty_level=level))


@when(
    parsers.parse('呼叫 query_cards tool 帶入 source_type "{source}" 和 tag "{tag}"'),
    target_fixture='tool_result',
)
def when_query_cards_composite(card_repo: AsyncMock, source: str, tag: str) -> Any:
    from persochattai.tools import create_query_cards_handler

    handler = create_query_cards_handler(card_repo)
    return _run(handler(source_type=source, tag=tag))


# --- When: create_card ---


@when('呼叫 create_card tool 帶入完整參數', target_fixture='tool_result')
def when_create_card_full(card_repo: AsyncMock, datatable: list[list[str]]) -> Any:
    from persochattai.tools import create_create_card_handler

    handler = create_create_card_handler(card_repo)
    params: dict[str, Any] = {}
    for row in datatable[1:]:
        key, value_str = row[0], row[1]
        if value_str.startswith('['):
            params[key] = json.loads(value_str)
        else:
            params[key] = value_str
    return _run(handler(**params))


@when('呼叫 create_card tool 缺少 title 欄位', target_fixture='tool_result')
def when_create_card_missing_title(card_repo: AsyncMock) -> Any:
    from persochattai.tools import create_create_card_handler

    handler = create_create_card_handler(card_repo)
    return _run(
        handler(
            summary='Some summary',
            keywords=[],
            source_type='podcast_bbc',
            difficulty_level='B1',
        )
    )


# --- When: get_user_history ---


@when('呼叫 get_user_history tool 帶入該使用者 ID', target_fixture='tool_result')
def when_get_user_history(assessment_service: AsyncMock, user_id: str) -> Any:
    from persochattai.tools import create_get_user_history_handler

    handler = create_get_user_history_handler(assessment_service)
    return _run(handler(user_id=user_id))


# --- When: tool registry ---


@when('查詢 content agent 的 tool 列表', target_fixture='tool_list')
def when_list_content_tools(card_repo: AsyncMock, assessment_service: AsyncMock) -> list[str]:
    from persochattai.tools import build_content_tool_registry

    registry = build_content_tool_registry(card_repo)
    return registry.list_tools()


@when('查詢 conversation agent 的 tool 列表', target_fixture='tool_list')
def when_list_conversation_tools(card_repo: AsyncMock, assessment_service: AsyncMock) -> list[str]:
    from persochattai.tools import build_conversation_tool_registry

    registry = build_conversation_tool_registry(card_repo, assessment_service)
    return registry.list_tools()


@when('查詢 assessment agent 的 tool 列表', target_fixture='tool_list')
def when_list_assessment_tools(card_repo: AsyncMock, assessment_service: AsyncMock) -> list[str]:
    from persochattai.tools import build_assessment_tool_registry

    registry = build_assessment_tool_registry(assessment_service)
    return registry.list_tools()


# --- Then: query_cards ---


@then(parsers.parse('回傳 {count:d} 張卡片且標題為 "{title}"'))
def then_cards_count_and_title(tool_result: Any, count: int, title: str) -> None:
    assert len(tool_result) == count
    assert tool_result[0]['title'] == title


@then('回傳空列表')
def then_empty_list(tool_result: Any) -> None:
    assert tool_result == []


# --- Then: create_card ---


@then(parsers.parse('卡片成功寫入且回傳含 "{field}" 欄位'))
def then_card_has_field(tool_result: Any, field: str) -> None:
    assert field in tool_result


@then(parsers.parse('回傳錯誤訊息包含 "{keyword}"'))
def then_error_contains(tool_result: Any, keyword: str) -> None:
    assert 'error' in tool_result
    assert keyword in tool_result['error']


# --- Then: get_user_history ---


@then(parsers.parse('回傳包含 "{k1}" 和 "{k2}" 和 "{k3}"'))
def then_result_has_keys(tool_result: Any, k1: str, k2: str, k3: str) -> None:
    assert k1 in tool_result
    assert k2 in tool_result
    assert k3 in tool_result


@then(parsers.parse('"{key}" 有 {count:d} 筆紀錄'))
def then_key_has_count(tool_result: Any, key: str, count: int) -> None:
    assert len(tool_result[key]) == count


@then(parsers.parse('回傳 "{key}" 為 null'))
def then_key_is_null(tool_result: Any, key: str) -> None:
    assert tool_result[key] is None


@then(parsers.parse('"{key}" 為空列表'))
def then_key_is_empty(tool_result: Any, key: str) -> None:
    assert tool_result[key] == []


# --- Then: tool registry ---


@then(parsers.parse('只包含 "{tool_name}"'))
def then_only_contains(tool_list: list[str], tool_name: str) -> None:
    assert tool_list == [tool_name]


@then(parsers.parse('包含 "{t1}" 和 "{t2}"'))
def then_contains_two(tool_list: list[str], t1: str, t2: str) -> None:
    assert set(tool_list) == {t1, t2}
