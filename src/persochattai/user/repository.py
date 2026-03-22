"""User DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import UserTable


def _row_to_dict(row: UserTable) -> dict[str, Any]:
    return {
        'id': str(row.id),
        'display_name': row.display_name,
        'current_level': row.current_level,
    }


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, display_name: str) -> dict[str, Any]:
        user = UserTable(id=uuid.uuid4(), display_name=display_name)
        self._session.add(user)
        await self._session.flush()
        return _row_to_dict(user)

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        stmt = select(UserTable).where(UserTable.id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None

    async def get_by_display_name(self, display_name: str) -> dict[str, Any] | None:
        stmt = select(UserTable).where(UserTable.display_name == display_name)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None
