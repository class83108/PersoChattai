"""Content DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import CardTable

logger = logging.getLogger(__name__)


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        card_id = card_data.get('id', str(uuid.uuid4()))
        source_url = card_data.get('source_url')

        stmt = insert(CardTable).values(
            id=card_id,
            source_type=card_data['source_type'],
            source_url=source_url,
            title=card_data['title'],
            summary=card_data['summary'],
            keywords=card_data.get('keywords', []),
            dialogue_snippets=card_data.get('dialogue_snippets', []),
            difficulty_level=card_data.get('difficulty_level'),
            tags=card_data.get('tags', []),
        )
        # ON CONFLICT (source_url) WHERE source_url IS NOT NULL DO NOTHING
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['source_url'],
            index_where=CardTable.source_url.isnot(None),
        )
        stmt = stmt.returning(CardTable)
        result = await self._session.execute(stmt)
        row = result.fetchone()
        await self._session.flush()
        if row is None:
            return {}
        return _row_to_dict(row[0])

    async def get_by_id(self, card_id: str) -> dict[str, Any] | None:
        stmt = select(CardTable).where(CardTable.id == card_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None

    async def list_cards(
        self,
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        stmt = select(CardTable)

        if source_type:
            stmt = stmt.where(CardTable.source_type == source_type)
        if difficulty:
            stmt = stmt.where(CardTable.difficulty_level == difficulty)
        if tag:
            stmt = stmt.where(literal(tag) == func.any(CardTable.tags))
        if keyword:
            pattern = f'%{keyword}%'
            stmt = stmt.where(CardTable.title.ilike(pattern) | CardTable.summary.ilike(pattern))

        stmt = stmt.order_by(CardTable.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_row_to_dict(row) for row in result.scalars().all()]

    async def exists_by_url(self, source_url: str) -> bool:
        stmt = select(func.count()).select_from(CardTable).where(CardTable.source_url == source_url)
        result = await self._session.execute(stmt)
        return bool(result.scalar())


def _row_to_dict(row: CardTable) -> dict[str, Any]:
    return {
        'id': row.id,
        'source_type': row.source_type,
        'source_url': row.source_url,
        'title': row.title,
        'summary': row.summary,
        'keywords': row.keywords,
        'dialogue_snippets': row.dialogue_snippets,
        'difficulty_level': row.difficulty_level,
        'tags': row.tags,
        'created_at': row.created_at,
    }
