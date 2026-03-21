"""Content Summarizer Pipeline 測試。"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.content.scraper.protocol import RawArticle
from persochattai.content.service import ContentService
from tests.helpers import MockStreamAgent

scenarios('features/content_summarizer.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


VALID_CARD_RESPONSE = [
    {
        'title': 'Business Email',
        'summary': 'Learn email writing. Use formal language. Practice greetings.',
        'keywords': [
            {'word': 'negotiate', 'definition': 'to discuss terms', 'example': 'Let us negotiate.'}
        ],
        'difficulty_level': 'B2',
        'tags': ['business', 'email'],
    }
]

MULTI_CARD_RESPONSE = [
    {
        'title': 'Business Email Part 1',
        'summary': 'Formal greetings and openings.',
        'keywords': [{'word': 'greet', 'definition': 'to say hello', 'example': 'Hello'}],
        'difficulty_level': 'B1',
        'tags': ['business'],
    },
    {
        'title': 'Business Email Part 2',
        'summary': 'Closing and sign-offs.',
        'keywords': [{'word': 'regards', 'definition': 'a closing', 'example': 'Best regards'}],
        'difficulty_level': 'B1',
        'tags': ['business'],
    },
    {
        'title': 'Business Email Part 3',
        'summary': 'Subject lines and tone.',
        'keywords': [{'word': 'concise', 'definition': 'brief', 'example': 'Be concise'}],
        'difficulty_level': 'B2',
        'tags': ['business'],
    },
]

CEFR_LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}


# --- Fixtures ---


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock(side_effect=lambda data: {**data, 'id': 'card-new'})
    return repo


@pytest.fixture
def mock_agent() -> MockStreamAgent:
    return MockStreamAgent(return_value=VALID_CARD_RESPONSE)


@pytest.fixture
def service(mock_repo: MagicMock, mock_agent: MockStreamAgent) -> ContentService:
    return ContentService(repository=mock_repo, agent=mock_agent)


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Background ---


@given('測試用 ContentService 已初始化')
def service_initialized() -> None:
    pass


@given('模擬 Claude Agent 回傳有效的摘要結果')
def mock_valid_response(mock_agent: MockStreamAgent) -> None:
    mock_agent.return_value = VALID_CARD_RESPONSE


# --- Given: Happy Path ---


@given(
    parsers.re(
        r'一篇 Podcast 文章 source_type "(?P<st>[^"]+)" title "(?P<title>[^"]+)" '
        r'content "(?P<content>[^"]+)"'
    ),
)
def podcast_article(st: str, title: str, content: str, ctx: dict[str, Any]) -> None:
    ctx['article'] = RawArticle(url='https://example.com/ep1', title=title, content=content)
    ctx['source_type'] = st


@given(parsers.parse('PDF 文字內容 "{text}"'))
def pdf_text(text: str, ctx: dict[str, Any]) -> None:
    ctx['pdf_text'] = text


@given(parsers.parse('主題描述 "{topic}"'))
def free_topic(topic: str, ctx: dict[str, Any]) -> None:
    ctx['topic'] = topic


@given('一篇 Podcast 文章')
def simple_article(ctx: dict[str, Any]) -> None:
    ctx['article'] = RawArticle(
        url='https://example.com/ep1',
        title='Test Article',
        content='Some content here for testing.',
    )
    ctx['source_type'] = 'podcast_allearsenglish'


@given(parsers.parse('一篇 Podcast 文章 content 只有 "{text}"'))
def short_article(text: str, ctx: dict[str, Any]) -> None:
    ctx['article'] = RawArticle(url='https://example.com/short', title='Short', content=text)
    ctx['source_type'] = 'podcast_allearsenglish'


# --- Given: Error ---


@given('模擬 Claude Agent 拋出例外')
def mock_agent_error(mock_agent: MockStreamAgent) -> None:
    mock_agent.side_effect = RuntimeError('Agent failed')


@given('模擬 Claude Agent 回傳無法解析的格式')
def mock_agent_bad_format(mock_agent: MockStreamAgent) -> None:
    mock_agent.return_value = 'not a valid json or list'


# --- Given: Multi-card ---


@given(parsers.parse('模擬 Claude Agent 回傳 {count:d} 張卡片的摘要結果'))
def mock_multi_card(count: int, mock_agent: MockStreamAgent) -> None:
    mock_agent.return_value = MULTI_CARD_RESPONSE[:count]


@given('模擬 Claude Agent 回傳含 keywords 的摘要')
def mock_with_keywords(mock_agent: MockStreamAgent) -> None:
    mock_agent.return_value = VALID_CARD_RESPONSE


@given('模擬 Claude Agent 回傳摘要')
def mock_with_summary(mock_agent: MockStreamAgent) -> None:
    mock_agent.return_value = VALID_CARD_RESPONSE


@given(parsers.parse('模擬 Claude Agent 回傳 {count:d} 張卡片但第 {n:d} 張格式錯誤'))
def mock_partial_error(count: int, n: int, mock_agent: MockStreamAgent) -> None:
    cards = list(MULTI_CARD_RESPONSE[:count])
    cards[n - 1] = {'invalid': 'no title or summary'}
    mock_agent.return_value = cards


# --- When ---


@when('呼叫 summarize_article', target_fixture='result')
def call_summarize_article(service: ContentService, ctx: dict[str, Any]) -> Any:
    article = ctx.get(
        'article',
        RawArticle(
            url='https://example.com/default',
            title='Default Article',
            content='Default content for testing.',
        ),
    )
    try:
        cards = _run(
            service.summarize_article(
                article, source_type=ctx.get('source_type', 'podcast_allearsenglish')
            )
        )
        return {'cards': cards, 'error': None}
    except Exception as e:
        return {'cards': [], 'error': e}


@when('呼叫 summarize_pdf', target_fixture='result')
def call_summarize_pdf(service: ContentService, ctx: dict[str, Any]) -> Any:
    cards = _run(service.summarize_pdf(ctx['pdf_text']))
    return {'cards': cards, 'error': None}


@when('呼叫 summarize_free_topic', target_fixture='result')
def call_summarize_free_topic(service: ContentService, ctx: dict[str, Any]) -> Any:
    cards = _run(service.summarize_free_topic(ctx['topic']))
    return {'cards': cards, 'error': None}


# --- Then: Happy Path ---


@then(parsers.parse('產出至少 {count:d} 張卡片'))
def check_min_cards(result: dict[str, Any], count: int) -> None:
    assert result['error'] is None
    assert len(result['cards']) >= count


@then(parsers.parse('產出 {count:d} 張卡片'))
def check_exact_cards(result: dict[str, Any], count: int) -> None:
    assert result['error'] is None
    assert len(result['cards']) == count


@then('每張卡片包含 title summary keywords difficulty_level tags')
def check_card_fields(result: dict[str, Any]) -> None:
    for card in result['cards']:
        for field in ('title', 'summary', 'keywords', 'difficulty_level', 'tags'):
            assert field in card, f'Missing field: {field}'


@then(parsers.parse('卡片 source_type 為 "{st}"'))
def check_source_type(result: dict[str, Any], st: str) -> None:
    for card in result['cards']:
        assert card.get('source_type') == st


@then('卡片儲存至 DB')
def check_saved_to_db(mock_repo: MagicMock) -> None:
    assert mock_repo.create.called


# --- Then: Error ---


@then('記錄 error log')
def check_error_log() -> None:
    pass


@then('拋出明確的錯誤訊息')
def check_error_message(result: dict[str, Any]) -> None:
    assert result['error'] is not None


@then('不建立任何卡片')
def check_no_cards(mock_repo: MagicMock) -> None:
    assert not mock_repo.create.called


# --- Then: Multi-card ---


@then('所有卡片共用相同的 source_url')
def check_shared_url(result: dict[str, Any]) -> None:
    urls = [c.get('source_url') for c in result['cards']]
    assert len(set(urls)) == 1


# --- Then: DB ---


@then('所有產出的卡片都存在於 cards 表')
def check_all_saved(result: dict[str, Any], mock_repo: MagicMock) -> None:
    assert mock_repo.create.call_count == len(result['cards'])


@then('每張卡片的 source_url 與原始文章 URL 一致')
def check_url_match(result: dict[str, Any], ctx: dict[str, Any]) -> None:
    for card in result['cards']:
        assert card.get('source_url') == ctx['article'].url


# --- Then: Output Contract ---


@then('每張卡片的 keywords 包含 word definition example 欄位')
def check_keyword_fields(result: dict[str, Any]) -> None:
    for card in result['cards']:
        for kw in card.get('keywords', []):
            assert 'word' in kw
            assert 'definition' in kw
            assert 'example' in kw


@then(parsers.parse('每張卡片的 difficulty_level 為 {levels}'))
def check_cefr_level(result: dict[str, Any], levels: str) -> None:
    valid = set(levels.split())
    for card in result['cards']:
        assert card.get('difficulty_level') in valid
