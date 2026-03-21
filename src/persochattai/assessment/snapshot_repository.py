"""Level snapshot DB repository。"""

from __future__ import annotations

from typing import Any

import asyncpg


class LevelSnapshotRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_snapshot(self, *, user_id: str, data: dict[str, Any]) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_level_snapshots (
                    user_id, snapshot_date, cefr_level,
                    avg_mtld, avg_vocd_d, vocabulary_size,
                    strengths, weaknesses, conversation_count
                ) VALUES ($1, CURRENT_DATE, $2, $3, $4, $5, $6, $7, $8)
                """,
                user_id,
                data.get('cefr_level'),
                data.get('avg_mtld'),
                data.get('avg_vocd_d'),
                data.get('vocabulary_size', 0),
                data.get('strengths', []),
                data.get('weaknesses', []),
                data.get('conversation_count', 0),
            )

    async def get_latest(self, user_id: str) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM user_level_snapshots
                WHERE user_id = $1
                ORDER BY snapshot_date DESC
                LIMIT 1
                """,
                user_id,
            )
            return dict(row) if row else None
