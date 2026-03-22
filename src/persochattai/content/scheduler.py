"""Content 爬蟲排程。"""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler

if TYPE_CHECKING:
    from persochattai.content.crawl_service import CrawlService

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL_HOURS = 6


class ContentScheduler:
    def __init__(self, interval_hours: int = _DEFAULT_INTERVAL_HOURS) -> None:
        self._scheduler = AsyncIOScheduler()
        self._interval_hours = interval_hours
        self._running = False
        self._crawl_service: CrawlService | None = None

    def set_crawl_service(self, crawl_service: CrawlService) -> None:
        self._crawl_service = crawl_service

    def start(self) -> None:
        self._scheduler.add_job(
            self._scrape_job,
            'interval',
            hours=self._interval_hours,
            id='scrape_podcasts',
            replace_existing=True,
        )
        with contextlib.suppress(RuntimeError):
            self._scheduler.start()
        self._running = True
        logger.info('ContentScheduler 已啟動，間隔 %d 小時', self._interval_hours)

    def shutdown(self) -> None:
        with contextlib.suppress(Exception):
            self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info('ContentScheduler 已關閉')

    def is_running(self) -> bool:
        return self._running

    def has_scrape_job(self) -> bool:
        return self._scheduler.get_job('scrape_podcasts') is not None

    async def _scrape_job(self) -> None:
        logger.info('開始執行爬蟲 job')
        if self._crawl_service is None:
            logger.warning('CrawlService 尚未設定，跳過排程')
            return
        result = await self._crawl_service.run_crawl_if_free()
        if result:
            logger.info(
                '爬蟲完成：新增 %d / 跳過 %d / 失敗 %d',
                result.total_new,
                result.total_skipped,
                result.total_failed,
            )
