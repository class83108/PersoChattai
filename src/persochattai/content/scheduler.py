"""Content 爬蟲排程。"""

from __future__ import annotations

import contextlib
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL_HOURS = 6


class ContentScheduler:
    def __init__(self, interval_hours: int = _DEFAULT_INTERVAL_HOURS) -> None:
        self._scheduler = AsyncIOScheduler()
        self._interval_hours = interval_hours
        self._running = False

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
