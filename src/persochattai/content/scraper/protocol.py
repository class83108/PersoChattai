"""Scraper Protocol 與共用 models。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class ArticleMeta(BaseModel):
    url: str
    title: str


class RawArticle(BaseModel):
    url: str
    title: str
    content: str


class ScraperError(Exception):
    """爬蟲錯誤。"""


@runtime_checkable
class ScraperProtocol(Protocol):
    source_type: str

    async def fetch_article_list(self) -> list[ArticleMeta]: ...

    async def fetch_article_content(self, url: str) -> RawArticle: ...
