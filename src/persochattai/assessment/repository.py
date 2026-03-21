"""Assessment DB repository。"""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg


class AssessmentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        assessment_id = data.get('id', str(uuid.uuid4()))
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO assessments (
                    id, conversation_id, user_id,
                    mtld, vocd_d, k1_ratio, k2_ratio, awl_ratio,
                    new_words_count, new_words,
                    avg_sentence_length, conjunction_ratio, self_correction_count,
                    subordinate_clause_ratio, tense_diversity, grammar_error_rate,
                    cefr_level, lexical_assessment, fluency_assessment, grammar_assessment,
                    suggestions, raw_analysis, created_at
                ) VALUES (
                    $1, $2, $3,
                    $4, $5, $6, $7, $8,
                    $9, $10,
                    $11, $12, $13,
                    $14, $15, $16,
                    $17, $18, $19, $20,
                    $21, $22, NOW()
                )
                RETURNING *
                """,
                assessment_id,
                data['conversation_id'],
                data['user_id'],
                data.get('mtld'),
                data.get('vocd_d'),
                data.get('k1_ratio'),
                data.get('k2_ratio'),
                data.get('awl_ratio'),
                len(data.get('new_words', [])),
                data.get('new_words', []),
                data.get('avg_sentence_length'),
                data.get('conjunction_ratio'),
                data.get('self_correction_count'),
                data.get('subordinate_clause_ratio'),
                data.get('tense_diversity'),
                data.get('grammar_error_count'),
                data.get('cefr_level'),
                data.get('lexical_assessment'),
                data.get('fluency_assessment'),
                data.get('grammar_assessment'),
                data.get('suggestions', []),
                json.dumps(data.get('raw_analysis')) if data.get('raw_analysis') else None,
            )
            return dict(row) if row else {}

    async def get_by_id(self, assessment_id: str) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM assessments WHERE id = $1',
                assessment_id,
            )
            return dict(row) if row else None

    async def list_by_user(
        self, user_id: str, *, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM assessments
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )
            return [dict(row) for row in rows]

    async def count_by_user(self, user_id: str) -> int:
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM assessments WHERE user_id = $1',
                user_id,
            )
            return int(count)
