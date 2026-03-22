"""爬蟲批次去重測試。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.content.crawl_service import CrawlService
from persochattai.content.scraper.protocol import ArticleMeta, RawArticle

scenarios('features/crawl_dedup.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class FakeScraper:
    """測試用 scraper。"""

    def __init__(self, source_type: str = 'podcast_allearsenglish') -> None:
        self.source_type = source_type
        self._articles: list[ArticleMeta] = []
        self._fail_urls: set[str] = set()
        self.fetch_content_call_count = 0

    async def fetch_article_list(self) -> list[ArticleMeta]:
        return self._articles

    async def fetch_article_content(self, url: str) -> RawArticle:
        self.fetch_content_call_count += 1
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

    def card_count(self) -> int:
        return len(self._cards)


# --- Fixtures ---


@pytest.fixture
def repo() -> InMemoryCardRepo:
    return InMemoryCardRepo()


@pytest.fixture
def scraper() -> FakeScraper:
    return FakeScraper()


@pytest.fixture
def scrapers(scraper: FakeScraper) -> list[FakeScraper]:
    return [scraper]


@pytest.fixture
def content_service_mock(repo: InMemoryCardRepo) -> AsyncMock:
    mock = AsyncMock()

    async def _summarize_and_save(article: Any, source_type: str = '') -> list[dict[str, Any]]:
        card_data = {
            'title': f'Summary of {article.title}',
            'summary': 'A summary',
            'source_type': source_type,
            'source_url': article.url,
            'keywords': [],
            'tags': [],
        }
        await repo.create(card_data)
        return [card_data]

    mock.summarize_article.side_effect = _summarize_and_save
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


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Rule: Happy path ---


@given('CrawlService 已初始化且有 1 個 scraper')
def init_1_scraper() -> None:
    pass


@given(parsers.parse('scraper 回傳 {n:d} 篇文章'))
def scraper_returns_n(n: int, scraper: FakeScraper) -> None:
    scraper._articles = [
        ArticleMeta(url=f'https://example.com/art{i}', title=f'Art {i}') for i in range(n)
    ]


@given(parsers.parse('其中 {n:d} 篇的 source_url 已存在於 DB'))
def n_urls_exist(n: int, scraper: FakeScraper, repo: InMemoryCardRepo) -> None:
    for i in range(n):
        repo._existing_urls.add(scraper._articles[i].url)


@given('所有 source_url 都不存在於 DB')
def no_urls_exist() -> None:
    pass


@given('所有 source_url 都已存在於 DB')
def all_urls_exist(scraper: FakeScraper, repo: InMemoryCardRepo) -> None:
    for art in scraper._articles:
        repo._existing_urls.add(art.url)


@when('呼叫 run_crawl', target_fixture='crawl_result')
def call_run_crawl(crawl_service: CrawlService) -> Any:
    return _run(crawl_service.run_crawl())


@then(parsers.parse('fetch_article_content 只被呼叫 {n:d} 次'))
def check_fetch_count(n: int, scraper: FakeScraper) -> None:
    assert scraper.fetch_content_call_count == n


@then(parsers.parse('fetch_article_content 被呼叫 {n:d} 次'))
def check_fetch_count_exact(n: int, scraper: FakeScraper) -> None:
    assert scraper.fetch_content_call_count == n


@then('fetch_article_content 不被呼叫')
def check_fetch_not_called(scraper: FakeScraper) -> None:
    assert scraper.fetch_content_call_count == 0


@then(parsers.parse('結果中該 source 的 new_count 為 {n:d}'))
def check_source_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].new_count == n


@then(parsers.parse('結果中該 source 的 skipped_count 為 {n:d}'))
def check_source_skipped(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].skipped_count == n


@then(parsers.parse('結果中該 source 的 failed_count 為 {n:d}'))
def check_source_failed(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].failed_count == n


# --- Rule: Error / Failure ---


@given(parsers.parse('scraper 回傳 {n:d} 篇新文章'))
def scraper_returns_n_new(n: int, scraper: FakeScraper) -> None:
    scraper._articles = [
        ArticleMeta(url=f'https://example.com/new{i}', title=f'New {i}') for i in range(n)
    ]


@given(parsers.parse('第 {idx:d} 篇的 fetch_article_content 拋出例外'))
def nth_fetch_fails(idx: int, scraper: FakeScraper) -> None:
    # idx is 1-based from feature file; articles are 0-based
    url = scraper._articles[idx - 1].url
    scraper._fail_urls.add(url)


# --- Rule: Input boundary ---


@given(parsers.parse('scraper 回傳 0 篇文章'))
def scraper_returns_0(scraper: FakeScraper) -> None:
    scraper._articles = []


@given('測試用 CardRepository 已初始化')
def card_repo_init() -> None:
    pass


@when('呼叫 filter_existing_urls 傳入空列表', target_fixture='filter_result')
def call_filter_empty(repo: InMemoryCardRepo) -> set[str]:
    return _run(repo.filter_existing_urls([]))


@then('回傳空 set')
def check_empty_set(filter_result: set[str]) -> None:
    assert filter_result == set()


# --- Rule: State mutation ---


@then(parsers.parse('DB 中新增 {n:d} 張卡片'))
def check_db_count(n: int, repo: InMemoryCardRepo) -> None:
    assert repo.card_count() == n


@given('第一次 run_crawl 已執行完成')
def first_run_done(crawl_service: CrawlService) -> None:
    _run(crawl_service.run_crawl())


@when('再次呼叫 run_crawl', target_fixture='crawl_result')
def call_run_crawl_again(crawl_service: CrawlService) -> Any:
    return _run(crawl_service.run_crawl())


@then(parsers.parse('第二次結果中 new_count 為 {n:d}'))
def check_second_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].new_count == n


@then(parsers.parse('第二次結果中 skipped_count 為 {n:d}'))
def check_second_skipped(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[0].skipped_count == n


# --- Rule: Output contract ---


@given('scraper 回傳 5 篇文章其中 2 篇已存在且 1 篇 fetch 會失敗')
def scraper_5_mixed(scraper: FakeScraper, repo: InMemoryCardRepo) -> None:
    scraper._articles = [
        ArticleMeta(url=f'https://example.com/mix{i}', title=f'Mix {i}') for i in range(5)
    ]
    # 2 existing
    repo._existing_urls.add('https://example.com/mix0')
    repo._existing_urls.add('https://example.com/mix1')
    # 1 will fail on fetch
    scraper._fail_urls.add('https://example.com/mix2')


@then(parsers.parse('結果中該 source 的 new_count + skipped_count + failed_count 等於 {n:d}'))
def check_total_equals(n: int, crawl_result: Any) -> None:
    s = crawl_result.sources[0]
    assert s.new_count + s.skipped_count + s.failed_count == n
