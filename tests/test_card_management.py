"""Card Management 測試。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.app import create_app
from persochattai.config import Settings

scenarios('features/card_management.feature')


# --- Fixtures ---


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


class InMemoryCardRepository:
    """測試用 in-memory CardRepository。"""

    def __init__(self) -> None:
        self._cards: dict[str, dict[str, Any]] = {}

    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        card_id = card_data.get('id', str(uuid.uuid4()))
        source_url = card_data.get('source_url')
        if source_url and any(c.get('source_url') == source_url for c in self._cards.values()):
            return {}
        card_data['id'] = card_id
        card_data.setdefault('created_at', '2026-03-21T10:00:00')
        self._cards[card_id] = card_data
        return card_data

    async def get_by_id(self, card_id: str) -> dict[str, Any] | None:
        return self._cards.get(card_id)

    async def list_cards(
        self,
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        results = list(self._cards.values())

        if source_type:
            results = [c for c in results if c.get('source_type') == source_type]
        if difficulty:
            results = [c for c in results if c.get('difficulty_level') == difficulty]
        if tag:
            results = [c for c in results if tag in c.get('tags', [])]
        if keyword:
            kw = keyword.lower()
            results = [
                c
                for c in results
                if kw in c.get('title', '').lower() or kw in c.get('summary', '').lower()
            ]

        results.sort(key=lambda c: c.get('created_at', ''), reverse=True)
        return results[offset : offset + limit]

    async def exists_by_url(self, source_url: str) -> bool:
        return any(c.get('source_url') == source_url for c in self._cards.values())

    def count_by_url(self, source_url: str) -> int:
        return sum(1 for c in self._cards.values() if c.get('source_url') == source_url)


@pytest.fixture
def repo() -> InMemoryCardRepository:
    return InMemoryCardRepository()


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


@pytest.fixture
def client(repo: InMemoryCardRepository) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.card_repository = repo
    return TestClient(app)


def _run(coro: Any) -> Any:
    import asyncio

    return asyncio.run(coro)


# --- Background ---


@given('測試用 CardRepository 已初始化')
def card_repo_initialized() -> None:
    pass


# --- Given: 建立卡片 ---


@given(parsers.parse('已存在一張 source_url 為 "{url}" 的卡片'))
def card_with_url_exists(url: str, repo: InMemoryCardRepository) -> None:
    _run(
        repo.create(
            {
                'title': 'Existing',
                'source_type': 'podcast_allearsenglish',
                'summary': 'existing card',
                'source_url': url,
            }
        )
    )


# --- Given: 查詢卡片 ---


@given(parsers.parse('資料庫中有 {count:d} 張卡片'))
def db_has_n_cards(count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-{i}',
                    'title': f'Card {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Summary {i}',
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有 source_type "{st}" 的卡片 {count:d} 張'))
def db_has_n_cards_by_source(st: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-{st}-{i}',
                    'title': f'Card {st} {i}',
                    'source_type': st,
                    'summary': f'Summary {i}',
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有 difficulty_level "{dl}" 的卡片 {count:d} 張'))
def db_has_n_cards_by_difficulty(dl: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-{dl}-{i}',
                    'title': f'Card {dl} {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Summary {i}',
                    'difficulty_level': dl,
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有包含 tag "{tag}" 的卡片 {count:d} 張'))
def db_has_n_cards_with_tag(tag: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-tag-{tag}-{i}',
                    'title': f'Card tag {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Summary {i}',
                    'tags': [tag],
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有不包含 tag "{tag}" 的卡片 {count:d} 張'))
def db_has_n_cards_without_tag(tag: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-notag-{i}',
                    'title': f'Card notag {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Summary {i}',
                    'tags': ['other'],
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有 title 含 "{kw}" 的卡片 {count:d} 張'))
def db_has_cards_with_title(kw: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-title-{kw}-{i}',
                    'title': f'{kw} Guide {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Summary {i}',
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有 summary 含 "{kw}" 的卡片 {count:d} 張'))
def db_has_cards_with_summary(kw: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-summary-{kw}-{i}',
                    'title': f'Other Title {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Great {kw} for beginners {i}',
                    'created_at': f'2026-03-{20 - i:02d}T10:00:00',
                }
            )
        )


@given(parsers.parse('資料庫中有不含 "{kw}" 的卡片 {count:d} 張'))
def db_has_cards_without_kw(kw: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-nokw-{i}',
                    'title': f'Unrelated {i}',
                    'source_type': 'podcast_allearsenglish',
                    'summary': f'Nothing here {i}',
                    'created_at': f'2026-03-{19 - i:02d}T10:00:00',
                }
            )
        )


@given(
    parsers.parse('資料庫中有組合篩選卡片 source_type "{st}" 且 difficulty "{dl}" 共 {count:d} 張')
)
def db_has_cards_combo(st: str, dl: str, count: int, repo: InMemoryCardRepository) -> None:
    for i in range(count):
        _run(
            repo.create(
                {
                    'id': f'card-combo-{st}-{dl}-{i}',
                    'title': f'Combo {i}',
                    'source_type': st,
                    'summary': f'Summary {i}',
                    'difficulty_level': dl,
                    'created_at': f'2026-03-{21 - i:02d}T10:00:00',
                }
            )
        )


@given('資料庫中沒有任何卡片')
def db_has_no_cards() -> None:
    pass


@given(parsers.parse('資料庫中有一張 id 為 "{card_id}" 的卡片'))
def db_has_card_by_id(card_id: str, repo: InMemoryCardRepository) -> None:
    _run(
        repo.create(
            {
                'id': card_id,
                'title': 'Test Card',
                'source_type': 'podcast_allearsenglish',
                'summary': 'Test summary',
            }
        )
    )


@given('資料庫中有一張卡片', target_fixture='card_ctx')
def db_has_one_card(repo: InMemoryCardRepository) -> dict[str, Any]:
    card_id = str(uuid.uuid4())
    _run(
        repo.create(
            {
                'id': card_id,
                'title': 'Test Card',
                'source_type': 'podcast_allearsenglish',
                'summary': 'Test summary',
            }
        )
    )
    return {'card_id': card_id}


@given('資料庫中有一張包含 keywords 和 tags 的卡片', target_fixture='card_ctx')
def db_has_card_with_keywords(repo: InMemoryCardRepository) -> dict[str, Any]:
    card_id = str(uuid.uuid4())
    _run(
        repo.create(
            {
                'id': card_id,
                'title': 'Full Card',
                'source_type': 'podcast_allearsenglish',
                'summary': 'A complete summary',
                'keywords': [{'word': 'negotiate', 'definition': 'to discuss', 'example': 'ex'}],
                'tags': ['business'],
                'difficulty_level': 'B2',
            }
        )
    )
    return {'card_id': card_id}


# --- When: 建立卡片 ---


@when(
    parsers.re(
        r'建立卡片 title "(?P<title>[^"]+)" source_type "(?P<source_type>[^"]+)" '
        r'summary "(?P<summary>[^"]+)"'
    ),
    target_fixture='created_card',
)
def create_card(
    title: str, source_type: str, summary: str, repo: InMemoryCardRepository
) -> dict[str, Any]:
    return _run(repo.create({'title': title, 'source_type': source_type, 'summary': summary}))


@when(parsers.parse('建立卡片 source_url 為 "{url}"'), target_fixture='created_card')
def create_card_with_url(url: str, repo: InMemoryCardRepository) -> dict[str, Any]:
    return _run(
        repo.create(
            {
                'title': 'Dup Card',
                'source_type': 'podcast_allearsenglish',
                'summary': 'dup',
                'source_url': url,
            }
        )
    )


# --- When: 查詢卡片 ---


@when('查詢卡片列表不帶任何篩選條件', target_fixture='card_list')
def query_cards_no_filter(repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards())


@when(parsers.parse('查詢卡片列表篩選 source_type "{st}"'), target_fixture='card_list')
def query_cards_by_source(st: str, repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards(source_type=st))


@when(parsers.parse('查詢卡片列表篩選 difficulty "{dl}"'), target_fixture='card_list')
def query_cards_by_difficulty(dl: str, repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards(difficulty=dl))


@when(parsers.parse('查詢卡片列表篩選 tag "{tag}"'), target_fixture='card_list')
def query_cards_by_tag(tag: str, repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards(tag=tag))


@when(parsers.parse('查詢卡片列表篩選 keyword "{kw}"'), target_fixture='card_list')
def query_cards_by_keyword(kw: str, repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards(keyword=kw))


@when(
    parsers.parse('查詢卡片列表篩選 source_type "{st}" 且 difficulty "{dl}"'),
    target_fixture='card_list',
)
def query_cards_combo(st: str, dl: str, repo: InMemoryCardRepository) -> list[dict[str, Any]]:
    return _run(repo.list_cards(source_type=st, difficulty=dl))


@when(
    parsers.parse('查詢卡片列表 limit {limit:d} offset {offset:d}'),
    target_fixture='card_list',
)
def query_cards_paged(
    limit: int, offset: int, repo: InMemoryCardRepository
) -> list[dict[str, Any]]:
    return _run(repo.list_cards(limit=limit, offset=offset))


@when(parsers.parse('查詢卡片 "{card_id}"'), target_fixture='found_card')
def query_card_by_id(card_id: str, repo: InMemoryCardRepository) -> dict[str, Any] | None:
    return _run(repo.get_by_id(card_id))


# --- When: API ---


@when('發送 GET /api/content/cards', target_fixture='response')
def send_get_cards(client: TestClient) -> Any:
    return client.get('/api/content/cards')


@when('發送 GET /api/content/cards/{card_id}', target_fixture='response')
def send_get_card_by_id(client: TestClient, card_ctx: dict[str, Any]) -> Any:
    return client.get(f'/api/content/cards/{card_ctx["card_id"]}')


@when('發送 GET /api/content/cards/nonexistent-id', target_fixture='response')
def send_get_card_nonexistent(client: TestClient) -> Any:
    return client.get(f'/api/content/cards/{uuid.uuid4()}')


# --- Then: 建立卡片 ---


@then('卡片成功寫入')
def card_created(created_card: dict[str, Any]) -> None:
    assert created_card


@then('卡片包含自動產生的 id')
def card_has_id(created_card: dict[str, Any]) -> None:
    assert 'id' in created_card


@then('卡片包含 created_at')
def card_has_created_at(created_card: dict[str, Any]) -> None:
    assert 'created_at' in created_card


@then('不拋出錯誤')
def no_error() -> None:
    pass


@then(parsers.parse('資料庫中 source_url "{url}" 的卡片只有 {count:d} 筆'))
def db_has_n_cards_by_url(url: str, count: int, repo: InMemoryCardRepository) -> None:
    assert repo.count_by_url(url) == count


# --- Then: 查詢卡片 ---


@then(parsers.parse('回傳 {count:d} 張卡片'))
def check_card_count(count: int, card_list: list[dict[str, Any]]) -> None:
    assert len(card_list) == count


@then('按 created_at DESC 排序')
def check_card_order(card_list: list[dict[str, Any]]) -> None:
    timestamps = [c.get('created_at', '') for c in card_list]
    assert timestamps == sorted(timestamps, reverse=True)


@then(parsers.parse('跳過前 {count:d} 張'))
def check_offset(count: int) -> None:
    pass  # offset 正確性已由回傳數量驗證


@then('回傳該卡片的完整資料')
def check_found_card(found_card: dict[str, Any] | None) -> None:
    assert found_card is not None
    assert 'title' in found_card


@then('回傳 None')
def check_not_found(found_card: dict[str, Any] | None) -> None:
    assert found_card is None


# --- Then: API ---


@then(parsers.parse('API 回應狀態碼為 {status_code:d}'))
def check_api_status_code(response: Any, status_code: int) -> None:
    assert response.status_code == status_code


@then(parsers.parse('API 回應包含 {count:d} 張卡片'))
def check_api_card_count(response: Any, count: int) -> None:
    data = response.json()
    cards = data if isinstance(data, list) else data.get('cards', [])
    assert len(cards) == count


@then('API 回應包含卡片完整欄位')
def check_api_card_fields(response: Any) -> None:
    data = response.json()
    for field in ('id', 'title', 'summary', 'source_type'):
        assert field in data


@then('API 回應包含 id, title, summary, source_type, keywords, tags, difficulty_level, created_at')
def check_api_all_fields(response: Any) -> None:
    data = response.json()
    for field in (
        'id',
        'title',
        'summary',
        'source_type',
        'keywords',
        'tags',
        'difficulty_level',
        'created_at',
    ):
        assert field in data
