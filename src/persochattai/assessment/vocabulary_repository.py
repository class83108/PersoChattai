"""User vocabulary DB repository。"""

from __future__ import annotations

from typing import Any

import asyncpg


class UserVocabularyRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def upsert_words(self, *, user_id: str, words: list[str], conversation_id: str) -> None:
        if not words:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO user_vocabulary (user_id, word, first_seen_conversation_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, word)
                DO UPDATE SET occurrence_count = user_vocabulary.occurrence_count + 1
                """,
                [(user_id, word, conversation_id) for word in words],
            )

    async def get_vocabulary_stats(self, user_id: str) -> dict[str, Any]:
        async with self._pool.acquire() as conn:
            total = await conn.fetchval(
                'SELECT COUNT(*) FROM user_vocabulary WHERE user_id = $1',
                user_id,
            )
            rows = await conn.fetch(
                """
                SELECT word FROM user_vocabulary
                WHERE user_id = $1
                ORDER BY first_seen_at DESC
                LIMIT 20
                """,
                user_id,
            )
            return {
                'total_words': int(total),
                'recent_words': [row['word'] for row in rows],
            }
