"""手動觸發爬蟲 API 測試。"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.app import create_app
from persochattai.config import Settings
from persochattai.content.crawl_service import CrawlService
from persochattai.content.scraper.protocol import ArticleMeta, RawArticle

scenarios('features/crawl_trigger.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Helpers ---


class FakeScraper:
    """測試用 scraper。"""

    def __init__(self, source_type: str, articles: list[ArticleMeta] | None = None) -> None:
        self.source_type = source_type
        self._articles = articles or []
        self._fail_list = False
        self.fetch_content_mock = AsyncMock(
            side_effect=lambda url: RawArticle(
                url=url, title=f'Article {url}', content=f'Content of {url}'
            )
        )

    async def fetch_article_list(self) -> list[ArticleMeta]:
        if self._fail_list:
            raise RuntimeError(f'{self.source_type} fetch failed')
        return self._articles

    async def fetch_article_content(self, url: str) -> RawArticle:
        return await self.fetch_content_mock(url)


class InMemoryCardRepo:
    """測試用 in-memory CardRepository。"""

    def __init__(self) -> None:
        self._cards: dict[str, dict[str, Any]] = {}
        self._existing_urls: set[str] = set()

    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        import uuid

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


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def client(crawl_service: CrawlService, repo: InMemoryCardRepo) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.card_repository = repo
    app.state.crawl_service = crawl_service
    return TestClient(app)


# --- Rule: Happy path ---


@given('CrawlService 已初始化且有 2 個 scraper')
def init_2_scrapers(scrapers: list[FakeScraper]) -> None:
    scrapers.clear()
    scrapers.append(FakeScraper('podcast_allearsenglish'))
    scrapers.append(FakeScraper('podcast_bbc'))


@given('每個 scraper 回傳 2 篇新文章')
def each_scraper_returns_2(scrapers: list[FakeScraper]) -> None:
    for i, s in enumerate(scrapers):
        s._articles = [
            ArticleMeta(url=f'https://example.com/{s.source_type}/a{j}', title=f'Art {j}')
            for j in range(i * 10, i * 10 + 2)
        ]


@given('每個 scraper 回傳 1 篇新文章')
def each_scraper_returns_1(scrapers: list[FakeScraper]) -> None:
    for i, s in enumerate(scrapers):
        s._articles = [
            ArticleMeta(url=f'https://example.com/{s.source_type}/a{i}', title=f'Art {i}')
        ]


@when('發送 POST /api/content/trigger-crawl 無 body', target_fixture='response')
def trigger_no_body(client: TestClient) -> Any:
    return client.post('/api/content/trigger-crawl')


@when(
    parsers.parse('發送 POST /api/content/trigger-crawl body 為 source_types {types}'),
    target_fixture='response',
)
def trigger_with_types(types: str, client: TestClient) -> Any:
    import json

    source_types = json.loads(types)
    return client.post('/api/content/trigger-crawl', json={'source_types': source_types})


@then(parsers.parse('API 回應狀態碼為 {code:d}'))
def check_status(code: int, response: Any) -> None:
    assert response.status_code == code


@then(parsers.parse('回應包含 {count:d} 個 source 的結果'))
def check_source_count(count: int, response: Any) -> None:
    data = response.json()
    assert len(data['sources']) == count


@then(parsers.parse('每個 source 的 new_count 為 {n:d}'))
def check_each_new_count(n: int, response: Any) -> None:
    for source in response.json()['sources']:
        assert source['new_count'] == n


@then('回應只包含 podcast_bbc 的結果')
def check_only_bbc(response: Any) -> None:
    data = response.json()
    assert len(data['sources']) == 1
    assert data['sources'][0]['source_type'] == 'podcast_bbc'


# --- Rule: Error / Failure ---


@given('CrawlService 已初始化')
def init_crawl_service() -> None:
    pass


@given('爬蟲正在執行中')
def crawl_running(crawl_service: CrawlService) -> None:
    _run(crawl_service._lock.acquire())


@given('第一個 scraper 的 fetch_article_list 拋出例外')
def first_scraper_fails(scrapers: list[FakeScraper]) -> None:
    scrapers[0]._fail_list = True


@given('第二個 scraper 回傳 2 篇新文章')
def second_scraper_returns_2(scrapers: list[FakeScraper]) -> None:
    scrapers[1]._articles = [
        ArticleMeta(url=f'https://example.com/bbc/b{j}', title=f'BBC {j}') for j in range(2)
    ]


@then(parsers.parse('回應訊息為「{msg}」'))
def check_message(msg: str, response: Any) -> None:
    assert msg in response.json()['detail']


@when('呼叫 run_crawl', target_fixture='crawl_result')
def call_run_crawl(crawl_service: CrawlService) -> Any:

    return _run(crawl_service.run_crawl())


@then('結果包含第一個 source 的 error 訊息')
def check_first_error(crawl_result: Any) -> None:
    assert crawl_result.sources[0].error is not None


@then(parsers.parse('結果包含第二個 source 的 new_count 為 {n:d}'))
def check_second_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.sources[1].new_count == n


# --- Rule: Input boundary ---


@then(parsers.parse('API 回應狀態碼為 422'))
def check_422(response: Any) -> None:
    assert response.status_code == 422


# --- Rule: Edge cases ---


@given('排程正在執行爬蟲 job')
def scheduler_running(crawl_service: CrawlService) -> None:
    _run(crawl_service._lock.acquire())


@given('手動觸發正在執行中')
def manual_running(crawl_service: CrawlService) -> None:
    _run(crawl_service._lock.acquire())


@when('排程觸發 _scrape_job', target_fixture='scrape_job_result')
def trigger_scrape_job(crawl_service: CrawlService) -> Any:
    return _run(crawl_service.run_crawl_if_free())


@then('記錄 warning log')
def check_warning() -> None:
    pass


@then('不拋出例外')
def check_no_exception(scrape_job_result: Any) -> None:
    assert scrape_job_result is None


# --- Rule: Output contract ---


@given('CrawlService 已初始化且有 1 個 scraper')
def init_1_scraper(scrapers: list[FakeScraper]) -> None:
    scrapers.clear()
    scrapers.append(FakeScraper('podcast_allearsenglish'))


@given('scraper 回傳 3 篇文章其中 1 篇已存在')
def scraper_3_articles_1_existing(scrapers: list[FakeScraper], repo: InMemoryCardRepo) -> None:
    scrapers[0]._articles = [
        ArticleMeta(url=f'https://example.com/art{i}', title=f'Art {i}') for i in range(3)
    ]
    repo._existing_urls.add('https://example.com/art0')


@then(parsers.parse('結果包含 started_at 非 None'))
def check_started(crawl_result: Any) -> None:
    assert crawl_result.started_at is not None


@then(parsers.parse('結果包含 finished_at 非 None'))
def check_finished(crawl_result: Any) -> None:
    assert crawl_result.finished_at is not None


@then(parsers.parse('結果包含 total_new 為 {n:d}'))
def check_total_new(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_new == n


@then(parsers.parse('結果包含 total_skipped 為 {n:d}'))
def check_total_skipped(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_skipped == n


@then(parsers.parse('結果包含 total_failed 為 {n:d}'))
def check_total_failed(n: int, crawl_result: Any) -> None:
    assert crawl_result.total_failed == n
