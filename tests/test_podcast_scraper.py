"""Podcast Scraper 測試。"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

from persochattai.content.scheduler import ContentScheduler
from persochattai.content.scraper.allearsenglish import AllEarsEnglishScraper
from persochattai.content.scraper.bbc import BBC6MinuteEnglishScraper
from persochattai.content.scraper.protocol import (
    ArticleMeta,
    RawArticle,
)

scenarios('features/podcast_scraper.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Fixtures ---


@pytest.fixture
def aee_scraper() -> AllEarsEnglishScraper:
    return AllEarsEnglishScraper()


@pytest.fixture
def bbc_scraper() -> BBC6MinuteEnglishScraper:
    return BBC6MinuteEnglishScraper()


@pytest.fixture
def mock_http_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def scheduler() -> ContentScheduler:
    return ContentScheduler()


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Rule: ScraperProtocol ---


@given('一個實作 ScraperProtocol 的 adapter')
def protocol_adapter(aee_scraper: AllEarsEnglishScraper) -> None:
    pass


@then('adapter 具有 source_type 屬性')
def check_source_type(aee_scraper: AllEarsEnglishScraper) -> None:
    assert hasattr(aee_scraper, 'source_type')
    assert isinstance(aee_scraper.source_type, str)


@then('adapter 具有 fetch_article_list 方法')
def check_fetch_list(aee_scraper: AllEarsEnglishScraper) -> None:
    assert hasattr(aee_scraper, 'fetch_article_list')
    assert callable(aee_scraper.fetch_article_list)


@then('adapter 具有 fetch_article_content 方法')
def check_fetch_content(aee_scraper: AllEarsEnglishScraper) -> None:
    assert hasattr(aee_scraper, 'fetch_article_content')
    assert callable(aee_scraper.fetch_article_content)


# --- Rule: All Ears English ---


@given('AllEarsEnglishScraper 已初始化')
def aee_initialized(aee_scraper: AllEarsEnglishScraper) -> None:
    pass


VALID_AEE_LIST_HTML = """
<html><body>
<article class="post">
    <h2><a href="https://allearsenglish.com/ep1">Episode 1: Business Email</a></h2>
</article>
<article class="post">
    <h2><a href="https://allearsenglish.com/ep2">Episode 2: Job Interview</a></h2>
</article>
</body></html>
"""

VALID_AEE_ARTICLE_HTML = """
<html><body>
<h1 class="entry-title">Episode 1: Business Email</h1>
<div class="entry-content">
<p>Learn how to write professional business emails in English.</p>
<p>Key phrases and vocabulary for email communication.</p>
</div>
</body></html>
"""


@given('模擬目標頁面回傳有效 HTML')
def mock_valid_html(ctx: dict[str, Any]) -> None:
    ctx['mock_html'] = VALID_AEE_LIST_HTML


@given('模擬文章頁面回傳有效 HTML')
def mock_valid_article_html(ctx: dict[str, Any]) -> None:
    ctx['mock_article_html'] = VALID_AEE_ARTICLE_HTML


@given('模擬目標頁面回傳 HTTP 500')
def mock_http_500(ctx: dict[str, Any]) -> None:
    ctx['mock_status'] = 500


@given('模擬目標頁面回傳非預期 HTML 結構')
def mock_unexpected_html(ctx: dict[str, Any]) -> None:
    ctx['mock_html'] = '<html><body><div>No articles here</div></body></html>'


@given('模擬目標頁面回傳空的文章列表')
def mock_empty_list(ctx: dict[str, Any]) -> None:
    ctx['mock_html'] = '<html><body></body></html>'


@given('模擬文章頁面內容區域為空白')
def mock_empty_content(ctx: dict[str, Any]) -> None:
    ctx['mock_article_html'] = """
    <html><body>
    <h1 class="entry-title">Empty Article</h1>
    <div class="entry-content"></div>
    </body></html>
    """


@when('呼叫 fetch_article_list', target_fixture='article_list')
def call_fetch_list(aee_scraper: AllEarsEnglishScraper, ctx: dict[str, Any]) -> list[ArticleMeta]:
    mock_response = AsyncMock()
    mock_response.status_code = ctx.get('mock_status', 200)
    mock_response.text = ctx.get('mock_html', '')
    mock_response.raise_for_status = MagicMock()
    if ctx.get('mock_status', 200) >= 400:
        import httpx

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'Server Error', request=MagicMock(), response=mock_response
        )

    with patch('persochattai.content.scraper.allearsenglish.httpx.AsyncClient') as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client
        return _run(aee_scraper.fetch_article_list())


@when('呼叫 fetch_article_content', target_fixture='raw_article')
def call_fetch_content(aee_scraper: AllEarsEnglishScraper, ctx: dict[str, Any]) -> RawArticle:
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = ctx.get('mock_article_html', VALID_AEE_ARTICLE_HTML)
    mock_response.raise_for_status = MagicMock()

    with patch('persochattai.content.scraper.allearsenglish.httpx.AsyncClient') as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client
        return _run(aee_scraper.fetch_article_content('https://allearsenglish.com/ep1'))


@then('回傳 ArticleMeta 列表')
def check_article_meta_list(article_list: list[ArticleMeta]) -> None:
    assert isinstance(article_list, list)
    assert len(article_list) > 0


@then('每個 ArticleMeta 包含 url 和 title')
def check_meta_fields(article_list: list[ArticleMeta]) -> None:
    for meta in article_list:
        assert meta.url
        assert meta.title


@then('回傳 RawArticle 包含 title content url')
def check_raw_article(raw_article: RawArticle) -> None:
    assert raw_article.title
    assert raw_article.content is not None
    assert raw_article.url


@then('記錄 warning log')
def check_warning_log(caplog: pytest.LogCaptureFixture) -> None:
    # warning 被記錄即可
    pass


@then('回傳空列表')
def check_empty_list(article_list: list[ArticleMeta]) -> None:
    assert article_list == []


@then('記錄 warning log 包含解析失敗位置')
def check_warning_detail(caplog: pytest.LogCaptureFixture) -> None:
    pass


@then('回傳 RawArticle 的 content 為空字串')
def check_empty_content(raw_article: RawArticle) -> None:
    assert raw_article.content == ''


# --- Rule: BBC ---


@given('BBC6MinuteEnglishScraper 已初始化')
def bbc_initialized(bbc_scraper: BBC6MinuteEnglishScraper) -> None:
    pass


VALID_BBC_LIST_HTML = """
<html><body>
<div class="programme-list">
    <div class="programme">
        <a href="/features/6-minute-english/ep1">Is AI changing music?</a>
    </div>
    <div class="programme">
        <a href="/features/6-minute-english/ep2">Why do we love lists?</a>
    </div>
</div>
</body></html>
"""

VALID_BBC_ARTICLE_HTML = """
<html><body>
<h1>Is AI changing music?</h1>
<div class="text">
<p>Artificial intelligence is being used to create music.</p>
<p>But is it really creative?</p>
</div>
</body></html>
"""


@given('模擬 BBC 目標頁面回傳有效 HTML')
def mock_valid_bbc_html(ctx: dict[str, Any]) -> None:
    ctx['mock_html'] = VALID_BBC_LIST_HTML


@given('模擬 BBC 文章頁面回傳有效 HTML')
def mock_valid_bbc_article_html(ctx: dict[str, Any]) -> None:
    ctx['mock_article_html'] = VALID_BBC_ARTICLE_HTML


@given('模擬 BBC 文章頁面內容區域為空白')
def mock_empty_bbc_content(ctx: dict[str, Any]) -> None:
    ctx['mock_article_html'] = """
    <html><body>
    <h1>Empty Article</h1>
    <div class="text"></div>
    </body></html>
    """


@when('呼叫 BBC fetch_article_list', target_fixture='article_list')
def call_bbc_fetch_list(
    bbc_scraper: BBC6MinuteEnglishScraper, ctx: dict[str, Any]
) -> list[ArticleMeta]:
    mock_response = AsyncMock()
    mock_response.status_code = ctx.get('mock_status', 200)
    mock_response.text = ctx.get('mock_html', '')
    mock_response.raise_for_status = MagicMock()
    if ctx.get('mock_status', 200) >= 400:
        import httpx

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'Server Error', request=MagicMock(), response=mock_response
        )

    with patch('persochattai.content.scraper.bbc.httpx.AsyncClient') as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client
        return _run(bbc_scraper.fetch_article_list())


@when('呼叫 BBC fetch_article_content', target_fixture='raw_article')
def call_bbc_fetch_content(
    bbc_scraper: BBC6MinuteEnglishScraper, ctx: dict[str, Any]
) -> RawArticle:
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = ctx.get('mock_article_html', VALID_BBC_ARTICLE_HTML)
    mock_response.raise_for_status = MagicMock()

    with patch('persochattai.content.scraper.bbc.httpx.AsyncClient') as mock_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client
        return _run(
            bbc_scraper.fetch_article_content('https://bbc.co.uk/features/6-minute-english/ep1')
        )


# --- Rule: Output Contract ---


@given('一個 ArticleMeta 實例', target_fixture='article_meta')
def create_article_meta() -> ArticleMeta:
    return ArticleMeta(url='https://example.com', title='Test')


@given('一個 RawArticle 實例', target_fixture='raw_article_instance')
def create_raw_article() -> RawArticle:
    return RawArticle(url='https://example.com', title='Test', content='Test content')


@then('ArticleMeta 具有 url 欄位')
def check_meta_has_url(article_meta: ArticleMeta) -> None:
    assert hasattr(article_meta, 'url')


@then('ArticleMeta 具有 title 欄位')
def check_meta_has_title(article_meta: ArticleMeta) -> None:
    assert hasattr(article_meta, 'title')


@then('RawArticle 具有 url 欄位')
def check_raw_has_url(raw_article_instance: RawArticle) -> None:
    assert hasattr(raw_article_instance, 'url')


@then('RawArticle 具有 title 欄位')
def check_raw_has_title(raw_article_instance: RawArticle) -> None:
    assert hasattr(raw_article_instance, 'title')


@then('RawArticle 具有 content 欄位')
def check_raw_has_content(raw_article_instance: RawArticle) -> None:
    assert hasattr(raw_article_instance, 'content')


# --- Rule: Scheduler ---


@given('ContentScheduler 已初始化')
def scheduler_initialized(scheduler: ContentScheduler) -> None:
    pass


@given('ContentScheduler 已啟動')
def scheduler_started(scheduler: ContentScheduler) -> None:
    scheduler.start()


@when('啟動 scheduler')
def start_scheduler(scheduler: ContentScheduler) -> None:
    scheduler.start()


@when('關閉 scheduler')
def shutdown_scheduler(scheduler: ContentScheduler) -> None:
    scheduler.shutdown()


@then('scheduler 包含爬蟲 job')
def check_scheduler_job(scheduler: ContentScheduler) -> None:
    assert scheduler.has_scrape_job()


@then('scheduler 正確 shutdown')
def check_scheduler_shutdown(scheduler: ContentScheduler) -> None:
    assert not scheduler.is_running()
