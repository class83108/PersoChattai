"""Level snapshot DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import UserLevelSnapshotTable


class LevelSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_snapshot(self, *, user_id: str, data: dict[str, Any]) -> None:
        row = UserLevelSnapshotTable(
            user_id=user_id,
            snapshot_date=datetime.now(tz=UTC).date(),
            cefr_level=data.get('cefr_level'),
            avg_mtld=data.get('avg_mtld'),
            avg_vocd_d=data.get('avg_vocd_d'),
            vocabulary_size=data.get('vocabulary_size', 0),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            conversation_count=data.get('conversation_count', 0),
        )
        self._session.add(row)
        await self._session.flush()

    async def get_latest(self, user_id: str) -> dict[str, Any] | None:
        stmt = (
            select(UserLevelSnapshotTable)
            .where(UserLevelSnapshotTable.user_id == user_id)
            .order_by(UserLevelSnapshotTable.snapshot_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            'id': row.id,
            'user_id': row.user_id,
            'snapshot_date': row.snapshot_date,
            'cefr_level': row.cefr_level,
            'avg_mtld': row.avg_mtld,
            'avg_vocd_d': row.avg_vocd_d,
            'vocabulary_size': row.vocabulary_size,
            'strengths': row.strengths,
            'weaknesses': row.weaknesses,
            'conversation_count': row.conversation_count,
            'created_at': row.created_at,
        }
