"""Conversation API schemas。"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ConversationStatus(StrEnum):
    PREPARING = 'preparing'
    CONNECTING = 'connecting'
    ACTIVE = 'active'
    ASSESSING = 'assessing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class SourceType(StrEnum):
    CARD = 'card'
    PDF = 'pdf'
    FREE_TOPIC = 'free_topic'


S = ConversationStatus

VALID_TRANSITIONS: dict[ConversationStatus, set[ConversationStatus]] = {
    S.PREPARING: {S.CONNECTING, S.FAILED, S.CANCELLED},
    S.CONNECTING: {S.ACTIVE, S.FAILED, S.CANCELLED},
    S.ACTIVE: {S.ASSESSING, S.FAILED, S.CANCELLED},
    S.ASSESSING: {S.COMPLETED, S.FAILED},
}


class StartConversationRequest(BaseModel):
    user_id: str = Field(min_length=1)
    source_type: SourceType
    source_ref: str = Field(min_length=1)


@runtime_checkable
class ConversationRepositoryProtocol(Protocol):
    async def create(
        self, conversation_id: str, user_id: str, source_type: str, source_ref: str
    ) -> None: ...

    async def update_status(self, conversation_id: str, status: str) -> None: ...

    async def save_transcript(
        self, conversation_id: str, transcript: list[dict[str, Any]]
    ) -> None: ...

    async def update_ended_at(self, conversation_id: str, ended_at: datetime) -> None: ...

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None: ...

    async def list_by_user(self, user_id: str) -> list[dict[str, Any]]: ...


ScenarioDesigner = Callable[..., Coroutine[Any, Any, str]]
