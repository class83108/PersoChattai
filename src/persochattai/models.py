"""Pydantic models — 對應 DB schema。"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    display_name: str
    current_level: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class KeywordEntry(BaseModel):
    word: str
    definition: str
    example: str = ''


class Card(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_type: str
    source_url: str | None = None
    title: str
    summary: str
    keywords: list[KeywordEntry] = Field(default_factory=list)
    dialogue_snippets: list[str] = Field(default_factory=list)
    difficulty_level: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class TranscriptEntry(BaseModel):
    role: str
    text: str
    timestamp: float | None = None


class Conversation(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    conversation_type: str
    source_type: str
    source_ref: str | None = None
    system_instruction: str | None = None
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    status: str = 'preparing'


class Assessment(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    # 量化指標
    mtld: float | None = None
    vocd_d: float | None = None
    k1_ratio: float | None = None
    k2_ratio: float | None = None
    awl_ratio: float | None = None
    new_words_count: int | None = None
    new_words: list[str] = Field(default_factory=list)
    avg_sentence_length: float | None = None
    conjunction_ratio: float | None = None
    self_correction_count: int | None = None
    subordinate_clause_ratio: float | None = None
    tense_diversity: int | None = None
    grammar_error_rate: float | None = None
    # 質性分析
    cefr_level: str | None = None
    lexical_assessment: str | None = None
    fluency_assessment: str | None = None
    grammar_assessment: str | None = None
    suggestions: list[str] = Field(default_factory=list)
    raw_analysis: dict | None = None  # type: ignore[type-arg]
    created_at: datetime = Field(default_factory=datetime.now)


class UserVocabulary(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    word: str
    first_seen_at: datetime = Field(default_factory=datetime.now)
    first_seen_conversation_id: uuid.UUID | None = None
    occurrence_count: int = 1


class UserLevelSnapshot(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    snapshot_date: date
    cefr_level: str | None = None
    avg_mtld: float | None = None
    avg_vocd_d: float | None = None
    vocabulary_size: int | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    conversation_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
