"""ConversationRepository 整合測試 — 接真實 PostgreSQL。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.conversation.repository import ConversationRepository
from persochattai.database.tables import UserTable


async def _create_user(session: AsyncSession) -> str:
    user_id = str(uuid.uuid4())
    session.add(UserTable(id=user_id, display_name='test-user'))
    await session.flush()
    return user_id


@pytest.mark.asyncio
class TestConversationRepositoryIntegration:
    async def test_create_and_get_by_id(self, session: AsyncSession) -> None:
        user_id = await _create_user(session)
        repo = ConversationRepository(session)
        conv_id = str(uuid.uuid4())

        await repo.create(conv_id, user_id, 'podcast', 'ep-1')
        await session.commit()

        result = await repo.get_by_id(conv_id)
        assert result is not None
        assert result['user_id'] == uuid.UUID(user_id)
        assert result['source_type'] == 'podcast'
        assert result['status'] == 'preparing'
        assert result['transcript'] == []

    async def test_update_status(self, session: AsyncSession) -> None:
        user_id = await _create_user(session)
        repo = ConversationRepository(session)
        conv_id = str(uuid.uuid4())

        await repo.create(conv_id, user_id, 'roleplay', 'ref-1')
        await repo.update_status(conv_id, 'active')
        await session.commit()

        result = await repo.get_by_id(conv_id)
        assert result is not None
        assert result['status'] == 'active'

    async def test_save_transcript(self, session: AsyncSession) -> None:
        user_id = await _create_user(session)
        repo = ConversationRepository(session)
        conv_id = str(uuid.uuid4())

        await repo.create(conv_id, user_id, 'podcast', 'ep-2')
        transcript = [
            {'role': 'user', 'text': 'Hello'},
            {'role': 'assistant', 'text': 'Hi there'},
        ]
        await repo.save_transcript(conv_id, transcript)
        await session.commit()

        result = await repo.get_by_id(conv_id)
        assert result is not None
        assert len(result['transcript']) == 2
        assert result['transcript'][0]['role'] == 'user'

    async def test_update_ended_at(self, session: AsyncSession) -> None:
        user_id = await _create_user(session)
        repo = ConversationRepository(session)
        conv_id = str(uuid.uuid4())

        await repo.create(conv_id, user_id, 'podcast', 'ep-3')
        now = datetime.now(tz=UTC)
        await repo.update_ended_at(conv_id, now)
        await session.commit()

        result = await repo.get_by_id(conv_id)
        assert result is not None
        assert result['ended_at'] is not None

    async def test_list_by_user(self, session: AsyncSession) -> None:
        user_id = await _create_user(session)
        repo = ConversationRepository(session)

        for i in range(3):
            await repo.create(str(uuid.uuid4()), user_id, 'podcast', f'ep-{i}')
        await session.commit()

        results = await repo.list_by_user(user_id)
        assert len(results) == 3
        assert all(r['source_type'] == 'podcast' for r in results)

    async def test_get_by_id_not_found(self, session: AsyncSession) -> None:
        repo = ConversationRepository(session)
        result = await repo.get_by_id(str(uuid.uuid4()))
        assert result is None
