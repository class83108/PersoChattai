"""SQLAlchemy ORM models — 對應全部 8 張 DB 表。"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from persochattai.database.base import Base


class UserTable(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    current_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CardTable(Base):
    __tablename__ = 'cards'
    __table_args__ = (
        Index(
            'idx_cards_source_url_unique',
            'source_url',
            unique=True,
            postgresql_where=text('source_url IS NOT NULL'),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    dialogue_snippets: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    difficulty_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default='{}')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ConversationTable(Base):
    __tablename__ = 'conversations'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    conversation_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="'preparing'")


class AssessmentTable(Base):
    __tablename__ = 'assessments'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    # 量化指標
    mtld: Mapped[float | None] = mapped_column(Float, nullable=True)
    vocd_d: Mapped[float | None] = mapped_column(Float, nullable=True)
    k1_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    k2_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    awl_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_words_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_words: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default='{}')
    avg_sentence_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    conjunction_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    self_correction_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subordinate_clause_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    tense_diversity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grammar_error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 質性分析
    cefr_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    lexical_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    fluency_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    grammar_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default='{}')
    raw_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserVocabularyTable(Base):
    __tablename__ = 'user_vocabulary'
    __table_args__ = (UniqueConstraint('user_id', 'word'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    word: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    first_seen_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=True
    )
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1')


class UserLevelSnapshotTable(Base):
    __tablename__ = 'user_level_snapshots'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    cefr_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    avg_mtld: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_vocd_d: Mapped[float | None] = mapped_column(Float, nullable=True)
    vocabulary_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default='{}')
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default='{}')
    conversation_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ApiUsageTable(Base):
    __tablename__ = 'api_usage'
    __table_args__ = (Index('idx_api_usage_type_created', 'usage_type', 'created_at'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usage_type: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_creation_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_read_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ModelConfigTable(Base):
    __tablename__ = 'model_config'
    __table_args__ = (
        Index('idx_model_config_provider', 'provider'),
        Index(
            'idx_model_config_active',
            'provider',
            'is_active',
            postgresql_where=True,  # partial index: WHERE is_active = TRUE
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')
    pricing: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
