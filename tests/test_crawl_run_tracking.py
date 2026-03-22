"""爬蟲執行紀錄測試。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.content.crawl_service import CrawlService
from persochattai.content.scraper.protocol import ArticleMeta, RawArticle

scenarios('features/crawl_run_tracking.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class FakeScraper:
    """測試用 scraper。"""

    def __init__(self, source_type: str, articles: list[ArticleMeta] | None = None) -> None:
        self.source_type = source_type
        self._articles = articles or []
        self._fail_list = False
        self._fail_urls: set[str] = set()

    async def fetch_article_list(self) -> list[ArticleMeta]:
        if self._fail_list:
            raise RuntimeError(f'{self.source_type} fetch failed')
        return self._articles

    async def fetch_article_content(self, url: str) -> RawArticle:
        if url in self._fail_urls:
            raise RuntimeError(f'Fetch failed for {url}')
        return RawArticle(url=url, title=f'Article {url}', content=f'Content of {url}')


class InMemoryCardRepo:
    """測試用 in-memory CardRepository。"""

    def __init__(self) -> None:
        self._cards: dict[str, dict[str, Any]] = {}
        self._existing_urls: set[str] = set()

    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        card_id = card_data.get('id', str(uuid.uuid4()))
        source_url = card_data.get('source_url')
        if source_url and source_url in self._existing_urls:
            return {}
        if source_url:
            self._existing_urls.add(source_url)
        card_data['id'] = card_id
        self._cards[card_id] = card_data
        return card_data

    async def filter_existing_urls(self, urls: list[str]) -> set[str]:
        return {u for u in urls if u in self._existing_urls}

    async def exists_by_url(self, source_url: str) -> bool:
        return source_url in self._existing_urls


# --- Fixtures ---


@pytest.fixture
def repo() -> InMemoryCardRepo:
    return InMemoryCardRepo()


@pytest.fixture
def scrapers() -> list[FakeScraper]:
    return []


@pytest.fixture
def content_service_mock() -> AsyncMock:
    mock = AsyncMock()
    mock.summarize_article.return_value = [
        {'title': 'Summary', 'summary': 'A summary', 'keywords': [], 'tags': []}
    ]
    return mock


@pytest.fixture
def crawl_service(
    scrapers: list[FakeScraper],
    repo: InMemoryCardRepo,
    content_service_mock: AsyncMock,
) -> CrawlService:
    return CrawlService(
        scrapers=scrapers,  # type: ignore[arg-type]
        repository=repo,  # type: ignore[arg-type]
        content_service=content_service_mock,
    )


# --- Rule: Happy path ---


@given('CrawlService 已初始化且有 2 個 scraper')
def init_2_scrapers(scrapers: list[FakeScraper]) -> None:
    scrapers.clear()
    scrapers.append(FakeScraper('podcast_allearsenglish'))
    scrapers.append(FakeScraper('podcast_bbc'))


@given(parsers.parse('第一個 scraper 回傳 {n:d} 篇新文章'))
def first_scraper_returns(n: int, scrapers: list[FakeScraper]) -> None:
    scrapers[0]._articles = [
        ArticleMeta(url=f'https://example.com/aee/a{i}', title=f'AEE {i}') for i in range(n)
    ]


@given(parsers.parse('第二個 scraper 回傳 {n:d} 篇新文章'))
def second_scraper_returns(n: int, scrapers: list[FakeScraper]) -> None:
    scrapers[1]._articles = [
        ArticleMeta(url=f'https://example.com/bbc/b{i}', title=f'BBC {i}') for i in range(n)
    ]


@when('呼叫 run_crawl', target_fixture='crawl_result')
def call_run_crawl(crawl_service: CrawlService) -> Any:
    return _run(crawl_service.run_crawl())


@then(parsers.parse('結果的 sources 包含 {n:d} 筆 SourceCrawlResult'))
def check_sources_count(n: int, crawl_result: Any) -> None:
    assert len(crawl_result.sources) == n


@then(parsers.parse('結果的 sources 包含 {n:d} 筆'))
def check_sources_count_short(n: int, crawl_result: Any) -> None:
    assert len(crawl_result.sources) == n


@then(parsers.parse('第一個 source 的 new_count 為 {n:d}'))
def check_first_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].new_count == n


@then(parsers.parse('第二個 source 的 new_count 為 {n:d}'))
def check_second_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[1].new_count == n


# --- Rule: Error / Failure ---


@given('第一個 scraper 的 fetch_article_list 拋出例外')
def first_fails(scrapers: list[FakeScraper]) -> None:
    scrapers[0]._fail_list = True


@then('第一個 source 的 error 不為 None')
def check_first_error(crawl_result: Any) -> None:
    assert crawl_result.sources[0].error is not None


# --- Rule: Output contract ---


@given(
    parsers.parse(
        '第一個 scraper 產出 new_count {new:d} skipped_count {skip:d} failed_count {fail:d}'
    )
)
def first_scraper_mixed(
    new: int, skip: int, fail: int, scrapers: list[FakeScraper], repo: InMemoryCardRepo
) -> None:
    total = new + skip + fail
    scrapers[0]._articles = [
        ArticleMeta(url=f'https://example.com/aee/m{i}', title=f'AEE M{i}') for i in range(total)
    ]
    for i in range(skip):
        repo._existing_urls.add(f'https://example.com/aee/m{i}')
    for i in range(skip, skip + fail):
        scrapers[0]._fail_urls.add(f'https://example.com/aee/m{i}')


@given(
    parsers.parse(
        '第二個 scraper 產出 new_count {new:d} skipped_count {skip:d} failed_count {fail:d}'
    )
)
def second_scraper_mixed(
    new: int, skip: int, fail: int, scrapers: list[FakeScraper], repo: InMemoryCardRepo
) -> None:
    total = new + skip + fail
    scrapers[1]._articles = [
        ArticleMeta(url=f'https://example.com/bbc/m{i}', title=f'BBC M{i}') for i in range(total)
    ]
    for i in range(skip):
        repo._existing_urls.add(f'https://example.com/bbc/m{i}')
    for i in range(skip, skip + fail):
        scrapers[1]._fail_urls.add(f'https://example.com/bbc/m{i}')


@given('CrawlService 已初始化且有 1 個 scraper')
def init_1_scraper(scrapers: list[FakeScraper]) -> None:
    scrapers.clear()
    scrapers.append(FakeScraper('podcast_allearsenglish'))


@then(parsers.parse('結果的 total_new 為 {n:d}'))
def check_total_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_new == n


@then(parsers.parse('結果的 total_skipped 為 {n:d}'))
def check_total_skipped(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_skipped == n


@then(parsers.parse('結果的 total_failed 為 {n:d}'))
def check_total_failed(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_failed == n


@then('結果的 started_at 非 None')
def check_started(crawl_result: Any) -> None:
    assert crawl_result.started_at is not None


@then('結果的 finished_at 非 None')
def check_finished(crawl_result: Any) -> None:
    assert crawl_result.finished_at is not None


@then('finished_at 晚於或等於 started_at')
def check_time_order(crawl_result: Any) -> None:
    assert crawl_result.finished_at >= crawl_result.started_at
