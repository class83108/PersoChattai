"""User vocabulary DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import UserVocabularyTable


class UserVocabularyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_words(self, *, user_id: str, words: list[str], conversation_id: str) -> None:
        if not words:
            return
        for word in words:
            stmt = insert(UserVocabularyTable).values(
                user_id=user_id,
                word=word,
                first_seen_conversation_id=conversation_id,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'word'],
                set_={'occurrence_count': UserVocabularyTable.occurrence_count + 1},
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def get_vocabulary_stats(self, user_id: str) -> dict[str, Any]:
        total_stmt = (
            select(func.count())
            .select_from(UserVocabularyTable)
            .where(UserVocabularyTable.user_id == user_id)
        )
        total_result = await self._session.execute(total_stmt)
        total = int(total_result.scalar() or 0)

        recent_stmt = (
            select(UserVocabularyTable.word)
            .where(UserVocabularyTable.user_id == user_id)
            .order_by(UserVocabularyTable.first_seen_at.desc())
            .limit(20)
        )
        recent_result = await self._session.execute(recent_stmt)
        return {
            'total_words': total,
            'recent_words': [row[0] for row in recent_result.all()],
        }
