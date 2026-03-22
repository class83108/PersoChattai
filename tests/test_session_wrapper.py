"""database/session_wrapper.py 單元測試。

驗證 wrapper 的 session-per-call 模式：
- 每次方法呼叫建立新 session
- 寫入操作會 commit
- 讀取操作不 commit
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from persochattai.database.session_wrapper import (
    AssessmentRepositoryWrapper,
    ConversationRepositoryWrapper,
    ModelConfigRepositoryWrapper,
    SnapshotRepositoryWrapper,
    UsageRepositoryWrapper,
    UserRepositoryWrapper,
    VocabularyRepositoryWrapper,
)


def _make_factory_and_session() -> tuple[MagicMock, AsyncMock]:
    """建立 mock factory 和 session。"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(spec=async_sessionmaker)
    mock_factory.return_value = mock_ctx

    return mock_factory, mock_session


# ---------------------------------------------------------------------------
# ConversationRepositoryWrapper
# ---------------------------------------------------------------------------


class TestConversationRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ConversationRepository')
    async def test_create_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ConversationRepositoryWrapper(factory)

        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        await wrapper.create('conv-1', 'user-1', 'podcast', 'ref-1')

        mock_repo.create.assert_awaited_once_with(
            'conv-1', 'user-1', 'podcast', 'ref-1', 'preparing'
        )
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ConversationRepository')
    async def test_get_by_id_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ConversationRepositoryWrapper(factory)

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = {'id': 'conv-1'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_by_id('conv-1')

        assert result == {'id': 'conv-1'}
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ConversationRepository')
    async def test_update_status_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ConversationRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.update_status('conv-1', 'active')
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ConversationRepository')
    async def test_save_transcript_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ConversationRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.save_transcript('conv-1', [{'role': 'user', 'text': 'hi'}])
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ConversationRepository')
    async def test_list_by_user_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ConversationRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.list_by_user.return_value = []
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.list_by_user('user-1')

        assert result == []
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# AssessmentRepositoryWrapper
# ---------------------------------------------------------------------------


class TestAssessmentRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.AssessmentRepository')
    async def test_create_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = AssessmentRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.create.return_value = {'id': 'a-1'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.create({'conversation_id': 'c-1'})

        assert result == {'id': 'a-1'}
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.AssessmentRepository')
    async def test_get_by_id_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = AssessmentRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_by_id('a-1')

        assert result is None
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.AssessmentRepository')
    async def test_count_by_user_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = AssessmentRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.count_by_user.return_value = 5
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.count_by_user('user-1')

        assert result == 5
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# VocabularyRepositoryWrapper
# ---------------------------------------------------------------------------


class TestVocabularyRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UserVocabularyRepository')
    async def test_upsert_words_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = VocabularyRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.upsert_words(user_id='u-1', words=['hello'], conversation_id='c-1')
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UserVocabularyRepository')
    async def test_get_vocabulary_stats_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = VocabularyRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_vocabulary_stats.return_value = {'total': 10}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_vocabulary_stats('u-1')

        assert result == {'total': 10}
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# SnapshotRepositoryWrapper
# ---------------------------------------------------------------------------


class TestSnapshotRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.LevelSnapshotRepository')
    async def test_create_snapshot_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = SnapshotRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.create_snapshot(user_id='u-1', data={'cefr_level': 'B1'})
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.LevelSnapshotRepository')
    async def test_get_latest_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = SnapshotRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_latest.return_value = {'cefr_level': 'B1'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_latest('u-1')

        assert result == {'cefr_level': 'B1'}
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# UsageRepositoryWrapper
# ---------------------------------------------------------------------------


class TestUsageRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UsageRepository')
    async def test_save_token_record_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UsageRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.save_token_record(MagicMock(), model='gpt-4')
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UsageRepository')
    async def test_load_token_records_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UsageRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.load_token_records.return_value = []
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.load_token_records(days=7)

        assert result == []
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UsageRepository')
    async def test_save_audio_record_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UsageRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.save_audio_record(MagicMock())
        session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# ModelConfigRepositoryWrapper
# ---------------------------------------------------------------------------


class TestModelConfigRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_seed_defaults_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.seed_defaults()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_list_models_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.list_models.return_value = []
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.list_models(provider='gemini')

        assert result == []
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_set_active_model_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.set_active_model(provider='gemini', model_id='gemini-2.0-flash')
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_create_model_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.create_model.return_value = {'model_id': 'new'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.create_model(MagicMock())

        assert result == {'model_id': 'new'}
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_delete_model_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo_cls.return_value = AsyncMock()

        await wrapper.delete_model('old-model')
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.ModelConfigRepository')
    async def test_get_active_model_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = ModelConfigRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_active_model.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_active_model('gemini')

        assert result is None
        session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# UserRepositoryWrapper
# ---------------------------------------------------------------------------


class TestUserRepositoryWrapper:
    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UserRepository')
    async def test_create_commits(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UserRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.create.return_value = {'id': 'u1', 'display_name': '小明'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.create('小明')

        mock_repo.create.assert_awaited_once_with('小明')
        session.commit.assert_awaited_once()
        assert result == {'id': 'u1', 'display_name': '小明'}

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UserRepository')
    async def test_get_by_id_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UserRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = {'id': 'u1', 'display_name': '小明'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_by_id('u1')

        assert result == {'id': 'u1', 'display_name': '小明'}
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    @patch('persochattai.database.session_wrapper.UserRepository')
    async def test_get_by_display_name_no_commit(self, mock_repo_cls: MagicMock) -> None:
        factory, session = _make_factory_and_session()
        wrapper = UserRepositoryWrapper(factory)
        mock_repo = AsyncMock()
        mock_repo.get_by_display_name.return_value = {'id': 'u1', 'display_name': '小明'}
        mock_repo_cls.return_value = mock_repo

        result = await wrapper.get_by_display_name('小明')

        assert result == {'id': 'u1', 'display_name': '小明'}
        session.commit.assert_not_awaited()
