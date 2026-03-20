"""Conversation API schemas。"""

from __future__ import annotations

from enum import StrEnum

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


VALID_TRANSITIONS: dict[str, set[str]] = {
    'preparing': {'connecting', 'failed', 'cancelled'},
    'connecting': {'active', 'failed', 'cancelled'},
    'active': {'assessing', 'failed', 'cancelled'},
    'assessing': {'completed', 'failed'},
}


class StartConversationRequest(BaseModel):
    user_id: str = Field(min_length=1)
    source_type: SourceType
    source_ref: str = Field(min_length=1)
