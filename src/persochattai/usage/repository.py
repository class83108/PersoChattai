"""Usage DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from agent_core.usage_monitor import UsageRecord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import ApiUsageTable
from persochattai.usage.schemas import AudioDirection, GeminiAudioRecord


class UsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_token_record(self, record: UsageRecord, *, model: str) -> None:
        row = ApiUsageTable(
            usage_type='token',
            model=model,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            cache_creation_input_tokens=record.cache_creation_input_tokens,
            cache_read_input_tokens=record.cache_read_input_tokens,
            created_at=record.timestamp,
        )
        self._session.add(row)
        await self._session.flush()

    async def save_audio_record(self, record: GeminiAudioRecord) -> None:
        row = ApiUsageTable(
            usage_type='audio',
            model=record.model,
            audio_duration_sec=record.audio_duration_sec,
            direction=record.direction,
            created_at=record.timestamp,
        )
        self._session.add(row)
        await self._session.flush()

    async def load_token_records(self, *, days: int = 30) -> list[UsageRecord]:
        cutoff = datetime.now().astimezone() - timedelta(days=days)
        stmt = (
            select(ApiUsageTable)
            .where(ApiUsageTable.usage_type == 'token')
            .where(ApiUsageTable.created_at >= cutoff)
            .order_by(ApiUsageTable.created_at)
        )
        result = await self._session.execute(stmt)
        return [
            UsageRecord(
                timestamp=row.created_at,
                input_tokens=row.input_tokens or 0,
                output_tokens=row.output_tokens or 0,
                cache_creation_input_tokens=row.cache_creation_input_tokens or 0,
                cache_read_input_tokens=row.cache_read_input_tokens or 0,
            )
            for row in result.scalars().all()
        ]

    async def load_audio_records(self, *, days: int = 30) -> list[GeminiAudioRecord]:
        cutoff = datetime.now().astimezone() - timedelta(days=days)
        stmt = (
            select(ApiUsageTable)
            .where(ApiUsageTable.usage_type == 'audio')
            .where(ApiUsageTable.created_at >= cutoff)
            .order_by(ApiUsageTable.created_at)
        )
        result = await self._session.execute(stmt)
        return [
            GeminiAudioRecord(
                timestamp=row.created_at,
                audio_duration_sec=row.audio_duration_sec or 0.0,
                direction=cast(AudioDirection, row.direction or 'input'),
                model=row.model or '',
            )
            for row in result.scalars().all()
        ]
