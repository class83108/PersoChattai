"""Conversation DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import ConversationTable

logger = logging.getLogger(__name__)


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        conversation_id: str,
        user_id: str,
        source_type: str,
        source_ref: str,
        status: str = 'preparing',
    ) -> None:
        row = ConversationTable(
            id=conversation_id,
            user_id=user_id,
            conversation_type=source_type,
            source_type=source_type,
            source_ref=source_ref,
            status=status,
        )
        self._session.add(row)
        await self._session.flush()

    async def update_status(self, conversation_id: str, status: str) -> None:
        stmt = (
            update(ConversationTable)
            .where(ConversationTable.id == conversation_id)
            .values(status=status)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def save_transcript(self, conversation_id: str, transcript: list[dict[str, Any]]) -> None:
        stmt = (
            update(ConversationTable)
            .where(ConversationTable.id == conversation_id)
            .values(transcript=transcript)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def update_ended_at(self, conversation_id: str, ended_at: datetime) -> None:
        stmt = (
            update(ConversationTable)
            .where(ConversationTable.id == conversation_id)
            .values(ended_at=ended_at)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None:
        stmt = select(ConversationTable).where(ConversationTable.id == conversation_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None

    async def list_by_user(self, user_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(ConversationTable)
            .where(ConversationTable.user_id == user_id)
            .order_by(ConversationTable.started_at.desc())
        )
        result = await self._session.execute(stmt)
        return [
            {
                'id': row.id,
                'status': row.status,
                'started_at': row.started_at,
                'ended_at': row.ended_at,
                'source_type': row.source_type,
            }
            for row in result.scalars().all()
        ]


def _row_to_dict(row: ConversationTable) -> dict[str, Any]:
    return {
        'id': row.id,
        'user_id': row.user_id,
        'conversation_type': row.conversation_type,
        'source_type': row.source_type,
        'source_ref': row.source_ref,
        'system_instruction': row.system_instruction,
        'started_at': row.started_at,
        'ended_at': row.ended_at,
        'transcript': row.transcript,
        'status': row.status,
    }
