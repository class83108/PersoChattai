"""Crawl Service — 爬蟲執行核心邏輯。"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, computed_field

from persochattai.content.scraper.protocol import ScraperProtocol

logger = logging.getLogger(__name__)


# --- Models ---


class SourceCrawlResult(BaseModel):
    source_type: str
    new_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    error: str | None = None


class CrawlRunResult(BaseModel):
    started_at: datetime
    finished_at: datetime
    sources: list[SourceCrawlResult]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_new(self) -> int:
        return sum(s.new_count for s in self.sources)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_skipped(self) -> int:
        return sum(s.skipped_count for s in self.sources)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_failed(self) -> int:
        return sum(s.failed_count for s in self.sources)


@runtime_checkable
class CrawlRepositoryProtocol(Protocol):
    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]: ...
    async def filter_existing_urls(self, urls: list[str]) -> set[str]: ...


@runtime_checkable
class ContentServiceProtocol(Protocol):
    async def summarize_article(
        self, article: Any, source_type: str = 'podcast_allearsenglish'
    ) -> list[dict[str, Any]]: ...


# --- Service ---


class CrawlBusyError(Exception):
    """爬蟲正在執行中。"""


class CrawlService:
    def __init__(
        self,
        scrapers: list[ScraperProtocol],
        repository: CrawlRepositoryProtocol,
        content_service: ContentServiceProtocol,
    ) -> None:
        self._scrapers = scrapers
        self._repo = repository
        self._content_service = content_service
        self._lock = asyncio.Lock()

    def get_source_types(self) -> list[str]:
        return [s.source_type for s in self._scrapers]

    async def run_crawl(
        self,
        source_types: list[str] | None = None,
    ) -> CrawlRunResult:
        if self._lock.locked():
            raise CrawlBusyError('爬蟲正在執行中，請稍後再試')
        async with self._lock:
            return await self._do_crawl(source_types)

    async def run_crawl_if_free(self) -> CrawlRunResult | None:
        if self._lock.locked():
            logger.warning('爬蟲 lock 已被佔用，跳過本次排程執行')
            return None
        return await self.run_crawl()

    async def _do_crawl(
        self,
        source_types: list[str] | None = None,
    ) -> CrawlRunResult:
        started_at = datetime.now(UTC)
        scrapers = self._scrapers
        if source_types:
            scrapers = [s for s in self._scrapers if s.source_type in source_types]

        sources: list[SourceCrawlResult] = []
        for scraper in scrapers:
            result = await self._crawl_source(scraper)
            sources.append(result)

        return CrawlRunResult(
            started_at=started_at,
            finished_at=datetime.now(UTC),
            sources=sources,
        )

    async def _crawl_source(self, scraper: ScraperProtocol) -> SourceCrawlResult:
        source_type = scraper.source_type
        try:
            articles = await scraper.fetch_article_list()
        except Exception as e:
            logger.warning('爬蟲 %s fetch_article_list 失敗: %s', source_type, e)
            return SourceCrawlResult(source_type=source_type, error=str(e))

        if not articles:
            return SourceCrawlResult(source_type=source_type)

        urls = [a.url for a in articles]
        existing_urls = await self._repo.filter_existing_urls(urls)

        new_articles = [a for a in articles if a.url not in existing_urls]
        skipped_count = len(existing_urls)

        new_count = 0
        failed_count = 0
        for article_meta in new_articles:
            try:
                content = await scraper.fetch_article_content(article_meta.url)
                cards = await self._content_service.summarize_article(content, source_type)
                saved = [c for c in cards if c]
                if saved:
                    new_count += 1
                else:
                    logger.warning(
                        '爬蟲 %s 文章 %s 摘要成功但寫入被跳過',
                        source_type,
                        article_meta.url,
                    )
                    failed_count += 1
            except Exception as e:
                logger.warning(
                    '爬蟲 %s 處理文章 %s 失敗: %s',
                    source_type,
                    article_meta.url,
                    e,
                )
                failed_count += 1

        return SourceCrawlResult(
            source_type=source_type,
            new_count=new_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
        )
