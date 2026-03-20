"""Conversation DB repository。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class ConversationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        conversation_id: str,
        user_id: str,
        source_type: str,
        source_ref: str,
        status: str = 'preparing',
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversations (id, user_id, source_type, source_ref, status, started_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                conversation_id,
                user_id,
                source_type,
                source_ref,
                status,
            )

    async def update_status(self, conversation_id: str, status: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                'UPDATE conversations SET status = $1 WHERE id = $2',
                status,
                conversation_id,
            )

    async def save_transcript(self, conversation_id: str, transcript: list[dict[str, Any]]) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                'UPDATE conversations SET transcript = $1 WHERE id = $2',
                json.dumps(transcript),
                conversation_id,
            )

    async def update_ended_at(self, conversation_id: str, ended_at: datetime) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                'UPDATE conversations SET ended_at = $1 WHERE id = $2',
                ended_at,
                conversation_id,
            )

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM conversations WHERE id = $1',
                conversation_id,
            )
            return dict(row) if row else None

    async def list_by_user(self, user_id: str) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, status, started_at, ended_at, source_type
                FROM conversations
                WHERE user_id = $1
                ORDER BY started_at DESC
                """,
                user_id,
            )
            return [dict(row) for row in rows]
