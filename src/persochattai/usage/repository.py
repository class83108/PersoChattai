"""Usage DB repository（asyncpg）。"""

from __future__ import annotations

import uuid

import asyncpg
from agent_core.usage_monitor import UsageRecord

from persochattai.usage.schemas import GeminiAudioRecord


class UsageRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save_token_record(self, record: UsageRecord, *, model: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.fetchrow(
                """
                INSERT INTO api_usage (
                    id, usage_type, model,
                    input_tokens, output_tokens,
                    cache_creation_input_tokens, cache_read_input_tokens,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                str(uuid.uuid4()),
                'token',
                model,
                record.input_tokens,
                record.output_tokens,
                record.cache_creation_input_tokens,
                record.cache_read_input_tokens,
                record.timestamp,
            )

    async def save_audio_record(self, record: GeminiAudioRecord) -> None:
        async with self._pool.acquire() as conn:
            await conn.fetchrow(
                """
                INSERT INTO api_usage (
                    id, usage_type, model,
                    audio_duration_sec, direction,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                str(uuid.uuid4()),
                'audio',
                record.model,
                record.audio_duration_sec,
                record.direction,
                record.timestamp,
            )

    async def load_token_records(self, *, days: int = 30) -> list[UsageRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT input_tokens, output_tokens,
                       cache_creation_input_tokens, cache_read_input_tokens,
                       created_at
                FROM api_usage
                WHERE usage_type = 'token'
                  AND created_at >= NOW() - ($1 || ' days')::INTERVAL
                ORDER BY created_at
                """,
                str(days),
            )
        return [
            UsageRecord(
                timestamp=row['created_at'],
                input_tokens=row['input_tokens'],
                output_tokens=row['output_tokens'],
                cache_creation_input_tokens=row['cache_creation_input_tokens'] or 0,
                cache_read_input_tokens=row['cache_read_input_tokens'] or 0,
            )
            for row in rows
        ]

    async def load_audio_records(self, *, days: int = 30) -> list[GeminiAudioRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT audio_duration_sec, direction, model, created_at
                FROM api_usage
                WHERE usage_type = 'audio'
                  AND created_at >= NOW() - ($1 || ' days')::INTERVAL
                ORDER BY created_at
                """,
                str(days),
            )
        return [
            GeminiAudioRecord(
                timestamp=row['created_at'],
                audio_duration_sec=row['audio_duration_sec'],
                direction=row['direction'],
                model=row['model'],
            )
            for row in rows
        ]
