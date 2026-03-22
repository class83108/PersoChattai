"""Content Service schemas。"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class CardFilter(BaseModel):
    source_type: str | None = None
    difficulty: str | None = None
    tag: str | None = None
    keyword: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CreateCardRequest(BaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_url: str | None = None
    keywords: list[dict[str, str]] = Field(default_factory=list)
    dialogue_snippets: list[str] = Field(default_factory=list)
    difficulty_level: str | None = None
    tags: list[str] = Field(default_factory=list)


class FreeTopicRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class TriggerCrawlRequest(BaseModel):
    source_types: list[str] | None = None


class UploadPdfResponse(BaseModel):
    cards: list[dict[str, Any]]
    truncated: bool = False


@runtime_checkable
class CardRepositoryProtocol(Protocol):
    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]: ...

    async def get_by_id(self, card_id: str) -> dict[str, Any] | None: ...

    async def list_cards(
        self,
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...

    async def exists_by_url(self, source_url: str) -> bool: ...

    async def filter_existing_urls(self, urls: list[str]) -> set[str]: ...
