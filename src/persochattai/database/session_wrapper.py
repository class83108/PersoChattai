"""Session-aware repository wrappers for long-lived services.

Long-lived services (ConversationManager, AssessmentService) hold repository
references that outlive a single request. These wrappers create a fresh
AsyncSession per method call, commit on success, and rollback on failure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from persochattai.assessment.repository import AssessmentRepository
from persochattai.content.repository import CardRepository
from persochattai.assessment.snapshot_repository import LevelSnapshotRepository
from persochattai.assessment.vocabulary_repository import UserVocabularyRepository
from persochattai.conversation.repository import ConversationRepository
from persochattai.usage.model_config_repository import ModelConfigRepository
from persochattai.usage.repository import UsageRepository


class _SessionMethodWrapper:
    """Base class providing session-per-call pattern."""

    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory


class ConversationRepositoryWrapper(_SessionMethodWrapper):
    async def create(
        self,
        conversation_id: str,
        user_id: str,
        source_type: str,
        source_ref: str,
        status: str = 'preparing',
    ) -> None:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            await repo.create(conversation_id, user_id, source_type, source_ref, status)
            await session.commit()

    async def update_status(self, conversation_id: str, status: str) -> None:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            await repo.update_status(conversation_id, status)
            await session.commit()

    async def save_transcript(self, conversation_id: str, transcript: list[dict[str, Any]]) -> None:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            await repo.save_transcript(conversation_id, transcript)
            await session.commit()

    async def update_ended_at(self, conversation_id: str, ended_at: datetime) -> None:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            await repo.update_ended_at(conversation_id, ended_at)
            await session.commit()

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            return await repo.get_by_id(conversation_id)

    async def list_by_user(self, user_id: str) -> list[dict[str, Any]]:
        async with self._factory() as session:
            repo = ConversationRepository(session)
            return await repo.list_by_user(user_id)


class AssessmentRepositoryWrapper(_SessionMethodWrapper):
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        async with self._factory() as session:
            repo = AssessmentRepository(session)
            result = await repo.create(data)
            await session.commit()
            return result

    async def get_by_id(self, assessment_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            repo = AssessmentRepository(session)
            return await repo.get_by_id(assessment_id)

    async def list_by_user(
        self, user_id: str, *, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        async with self._factory() as session:
            repo = AssessmentRepository(session)
            return await repo.list_by_user(user_id, limit=limit, offset=offset)

    async def count_by_user(self, user_id: str) -> int:
        async with self._factory() as session:
            repo = AssessmentRepository(session)
            return await repo.count_by_user(user_id)


class VocabularyRepositoryWrapper(_SessionMethodWrapper):
    async def upsert_words(self, *, user_id: str, words: list[str], conversation_id: str) -> None:
        async with self._factory() as session:
            repo = UserVocabularyRepository(session)
            await repo.upsert_words(user_id=user_id, words=words, conversation_id=conversation_id)
            await session.commit()

    async def get_vocabulary_stats(self, user_id: str) -> dict[str, Any]:
        async with self._factory() as session:
            repo = UserVocabularyRepository(session)
            return await repo.get_vocabulary_stats(user_id)


class SnapshotRepositoryWrapper(_SessionMethodWrapper):
    async def create_snapshot(self, *, user_id: str, data: dict[str, Any]) -> None:
        async with self._factory() as session:
            repo = LevelSnapshotRepository(session)
            await repo.create_snapshot(user_id=user_id, data=data)
            await session.commit()

    async def get_latest(self, user_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            repo = LevelSnapshotRepository(session)
            return await repo.get_latest(user_id)


class CardRepositoryWrapper(_SessionMethodWrapper):
    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        async with self._factory() as session:
            repo = CardRepository(session)
            result = await repo.create(card_data)
            await session.commit()
            return result

    async def get_by_id(self, card_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            repo = CardRepository(session)
            return await repo.get_by_id(card_id)

    async def list_cards(
        self,
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with self._factory() as session:
            repo = CardRepository(session)
            return await repo.list_cards(
                source_type=source_type,
                difficulty=difficulty,
                tag=tag,
                keyword=keyword,
                limit=limit,
                offset=offset,
            )

    async def exists_by_url(self, source_url: str) -> bool:
        async with self._factory() as session:
            repo = CardRepository(session)
            return await repo.exists_by_url(source_url)


class UsageRepositoryWrapper(_SessionMethodWrapper):
    async def save_token_record(self, record: Any, *, model: str) -> None:
        async with self._factory() as session:
            repo = UsageRepository(session)
            await repo.save_token_record(record, model=model)
            await session.commit()

    async def save_audio_record(self, record: Any) -> None:
        async with self._factory() as session:
            repo = UsageRepository(session)
            await repo.save_audio_record(record)
            await session.commit()

    async def load_token_records(self, *, days: int = 30) -> list[Any]:
        async with self._factory() as session:
            repo = UsageRepository(session)
            return await repo.load_token_records(days=days)

    async def load_audio_records(self, *, days: int = 30) -> list[Any]:
        async with self._factory() as session:
            repo = UsageRepository(session)
            return await repo.load_audio_records(days=days)


class ModelConfigRepositoryWrapper(_SessionMethodWrapper):
    async def seed_defaults(self) -> None:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            await repo.seed_defaults()
            await session.commit()

    async def list_models(self, *, provider: str | None = None) -> list[Any]:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            return await repo.list_models(provider=provider)

    async def get_model(self, model_id: str) -> Any | None:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            return await repo.get_model(model_id)

    async def get_active_model(self, provider: str) -> Any | None:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            return await repo.get_active_model(provider)

    async def set_active_model(self, *, provider: str, model_id: str) -> None:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            await repo.set_active_model(provider=provider, model_id=model_id)
            await session.commit()

    async def create_model(self, model: Any) -> Any:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            result = await repo.create_model(model)
            await session.commit()
            return result

    async def update_model(self, model_id: str, updates: dict[str, Any]) -> Any:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            result = await repo.update_model(model_id, updates)
            await session.commit()
            return result

    async def delete_model(self, model_id: str) -> None:
        async with self._factory() as session:
            repo = ModelConfigRepository(session)
            await repo.delete_model(model_id)
            await session.commit()
