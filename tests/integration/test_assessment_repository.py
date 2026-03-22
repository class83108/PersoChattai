"""Assessment + Vocabulary + Snapshot Repository 整合測試。"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.assessment.repository import AssessmentRepository
from persochattai.assessment.snapshot_repository import LevelSnapshotRepository
from persochattai.assessment.vocabulary_repository import UserVocabularyRepository
from persochattai.database.tables import ConversationTable, UserTable


async def _create_user_and_conversation(session: AsyncSession) -> tuple[str, str]:
    """建立測試用 user + conversation，回傳 (user_id, conversation_id)。"""
    user_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())
    session.add(UserTable(id=user_id, display_name='test-user'))
    await session.flush()
    session.add(
        ConversationTable(
            id=conv_id,
            user_id=user_id,
            conversation_type='podcast',
            source_type='podcast',
            source_ref='ep-1',
        )
    )
    await session.flush()
    return user_id, conv_id


@pytest.mark.asyncio
class TestAssessmentRepositoryIntegration:
    async def test_create_and_get_by_id(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = AssessmentRepository(session)

        result = await repo.create(
            {
                'conversation_id': conv_id,
                'user_id': user_id,
                'mtld': 45.2,
                'vocd_d': 60.1,
                'k1_ratio': 0.65,
                'cefr_level': 'B1',
                'suggestions': ['多用複雜句型', '增加學術詞彙'],
                'new_words': ['pragmatic', 'nuanced'],
            }
        )
        await session.commit()

        assert result['cefr_level'] == 'B1'
        assert result['new_words_count'] == 2

        fetched = await repo.get_by_id(str(result['id']))
        assert fetched is not None
        assert fetched['mtld'] == pytest.approx(45.2)
        assert fetched['suggestions'] == ['多用複雜句型', '增加學術詞彙']

    async def test_list_by_user(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = AssessmentRepository(session)

        for _i in range(3):
            await repo.create(
                {
                    'conversation_id': conv_id,
                    'user_id': user_id,
                    'cefr_level': 'B1',
                }
            )
        await session.commit()

        results = await repo.list_by_user(user_id, limit=2)
        assert len(results) == 2

        all_results = await repo.list_by_user(user_id)
        assert len(all_results) == 3

    async def test_count_by_user(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = AssessmentRepository(session)

        assert await repo.count_by_user(user_id) == 0

        await repo.create({'conversation_id': conv_id, 'user_id': user_id})
        await repo.create({'conversation_id': conv_id, 'user_id': user_id})
        await session.commit()

        assert await repo.count_by_user(user_id) == 2


@pytest.mark.asyncio
class TestVocabularyRepositoryIntegration:
    async def test_upsert_new_words(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = UserVocabularyRepository(session)

        await repo.upsert_words(
            user_id=user_id,
            words=['hello', 'world', 'pragmatic'],
            conversation_id=conv_id,
        )
        await session.commit()

        stats = await repo.get_vocabulary_stats(user_id)
        assert stats['total_words'] == 3
        assert set(stats['recent_words']) == {'hello', 'world', 'pragmatic'}

    async def test_upsert_increments_occurrence(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = UserVocabularyRepository(session)

        await repo.upsert_words(user_id=user_id, words=['hello'], conversation_id=conv_id)
        await session.commit()

        # 再次 upsert 同一個字
        await repo.upsert_words(user_id=user_id, words=['hello'], conversation_id=conv_id)
        await session.commit()

        stats = await repo.get_vocabulary_stats(user_id)
        assert stats['total_words'] == 1  # 還是 1 個字，不是 2

    async def test_upsert_empty_words_noop(self, session: AsyncSession) -> None:
        user_id, conv_id = await _create_user_and_conversation(session)
        repo = UserVocabularyRepository(session)

        await repo.upsert_words(user_id=user_id, words=[], conversation_id=conv_id)
        await session.commit()

        stats = await repo.get_vocabulary_stats(user_id)
        assert stats['total_words'] == 0


@pytest.mark.asyncio
class TestSnapshotRepositoryIntegration:
    async def test_create_and_get_latest(self, session: AsyncSession) -> None:
        user_id, _ = await _create_user_and_conversation(session)
        repo = LevelSnapshotRepository(session)

        await repo.create_snapshot(
            user_id=user_id,
            data={
                'cefr_level': 'B1',
                'avg_mtld': 45.0,
                'vocabulary_size': 200,
                'strengths': ['fluency'],
                'weaknesses': ['grammar'],
            },
        )
        await session.commit()

        latest = await repo.get_latest(user_id)
        assert latest is not None
        assert latest['cefr_level'] == 'B1'
        assert latest['avg_mtld'] == pytest.approx(45.0)
        assert latest['strengths'] == ['fluency']
        assert latest['weaknesses'] == ['grammar']

    async def test_get_latest_returns_none_when_empty(self, session: AsyncSession) -> None:
        user_id, _ = await _create_user_and_conversation(session)
        repo = LevelSnapshotRepository(session)

        result = await repo.get_latest(user_id)
        assert result is None
