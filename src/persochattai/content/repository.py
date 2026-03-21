"""Content DB repository。"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class CardRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, card_data: dict[str, Any]) -> dict[str, Any]:
        card_id = card_data.get('id', str(uuid.uuid4()))
        source_url = card_data.get('source_url')
        keywords = card_data.get('keywords', [])
        dialogue_snippets = card_data.get('dialogue_snippets', [])
        tags = card_data.get('tags', [])

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO cards (id, source_type, source_url, title, summary,
                    keywords, dialogue_snippets, difficulty_level, tags, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                ON CONFLICT (source_url) WHERE source_url IS NOT NULL DO NOTHING
                RETURNING *
                """,
                card_id,
                card_data['source_type'],
                source_url,
                card_data['title'],
                card_data['summary'],
                json.dumps(keywords),
                json.dumps(dialogue_snippets),
                card_data.get('difficulty_level'),
                tags,
            )
            if row is None:
                return {}
            return dict(row)

    async def get_by_id(self, card_id: str) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM cards WHERE id = $1', card_id)
            return dict(row) if row else None

    async def list_cards(
        self,
        source_type: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if source_type:
            conditions.append(f'source_type = ${idx}')
            params.append(source_type)
            idx += 1
        if difficulty:
            conditions.append(f'difficulty_level = ${idx}')
            params.append(difficulty)
            idx += 1
        if tag:
            conditions.append(f'${idx} = ANY(tags)')
            params.append(tag)
            idx += 1
        if keyword:
            conditions.append(f'(title ILIKE ${idx} OR summary ILIKE ${idx})')
            params.append(f'%{keyword}%')
            idx += 1

        where = f'WHERE {" AND ".join(conditions)}' if conditions else ''
        params.extend([limit, offset])

        query = f"""
            SELECT * FROM cards
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def exists_by_url(self, source_url: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchval(
                'SELECT EXISTS(SELECT 1 FROM cards WHERE source_url = $1)',
                source_url,
            )
            return bool(row)
