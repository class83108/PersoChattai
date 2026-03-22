"""UsageRepository + ModelConfigRepository 整合測試。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from agent_core.usage_monitor import UsageRecord
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.usage.model_config_repository import (
    ActiveModelDeleteError,
    DuplicateModelError,
    ModelConfigRepository,
    ModelNotFoundError,
)
from persochattai.usage.repository import UsageRepository
from persochattai.usage.schemas import GeminiAudioRecord, ModelConfig


@pytest.mark.asyncio
class TestUsageRepositoryIntegration:
    async def test_save_and_load_token_records(self, session: AsyncSession) -> None:
        repo = UsageRepository(session)
        record = UsageRecord(
            timestamp=datetime.now(tz=UTC),
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=10,
            cache_read_input_tokens=5,
        )
        await repo.save_token_record(record, model='claude-sonnet-4')
        await session.commit()

        records = await repo.load_token_records(days=1)
        assert len(records) >= 1
        assert records[-1].input_tokens == 100
        assert records[-1].output_tokens == 50

    async def test_save_and_load_audio_records(self, session: AsyncSession) -> None:
        repo = UsageRepository(session)
        record = GeminiAudioRecord(
            timestamp=datetime.now(tz=UTC),
            audio_duration_sec=30.5,
            direction='input',
            model='gemini-2.0-flash',
        )
        await repo.save_audio_record(record)
        await session.commit()

        records = await repo.load_audio_records(days=1)
        assert len(records) >= 1
        assert records[-1].audio_duration_sec == 30.5
        assert records[-1].direction == 'input'


@pytest.mark.asyncio
class TestModelConfigRepositoryIntegration:
    async def test_seed_defaults(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        models = await repo.list_models()
        assert len(models) == 5  # 3 claude + 2 gemini

    async def test_seed_defaults_idempotent(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        # 第二次 seed 不應增加
        await repo.seed_defaults()
        await session.commit()

        models = await repo.list_models()
        assert len(models) == 5

    async def test_get_active_model(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        active = await repo.get_active_model('claude')
        assert active is not None
        assert active.is_active is True
        assert active.provider == 'claude'

    async def test_set_active_model(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        await repo.set_active_model(provider='claude', model_id='claude-haiku-4-20250514')
        await session.commit()

        active = await repo.get_active_model('claude')
        assert active is not None
        assert active.model_id == 'claude-haiku-4-20250514'

        # 舊的不再 active
        old = await repo.get_model('claude-sonnet-4-20250514')
        assert old is not None
        assert old.is_active is False

    async def test_set_active_model_not_found_raises(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        with pytest.raises(ModelNotFoundError):
            await repo.set_active_model(provider='claude', model_id='nonexistent')

    async def test_create_model(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        model = ModelConfig(
            id='',
            provider='test',
            model_id='test-model-1',
            display_name='Test Model',
            is_active=False,
            pricing={'input': 1.0, 'output': 2.0},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        result = await repo.create_model(model)
        await session.commit()

        assert result.model_id == 'test-model-1'
        assert result.display_name == 'Test Model'

    async def test_create_duplicate_model_raises(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        model = ModelConfig(
            id='',
            provider='test',
            model_id='dup-model',
            display_name='Dup',
            is_active=False,
            pricing={'input': 1.0},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create_model(model)
        await session.commit()

        with pytest.raises(DuplicateModelError):
            await repo.create_model(model)

    async def test_update_model(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        model = ModelConfig(
            id='',
            provider='test',
            model_id='upd-model',
            display_name='Before',
            is_active=False,
            pricing={'input': 1.0},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create_model(model)
        await session.commit()

        updated = await repo.update_model('upd-model', {'display_name': 'After'})
        assert updated.display_name == 'After'

    async def test_delete_model(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        model = ModelConfig(
            id='',
            provider='test',
            model_id='del-model',
            display_name='Delete Me',
            is_active=False,
            pricing={'input': 1.0},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create_model(model)
        await session.commit()

        await repo.delete_model('del-model')
        await session.commit()

        assert await repo.get_model('del-model') is None

    async def test_delete_active_model_raises(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        model = ModelConfig(
            id='',
            provider='test',
            model_id='active-no-del',
            display_name='Active',
            is_active=True,
            pricing={'input': 1.0},
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create_model(model)
        await session.commit()

        with pytest.raises(ActiveModelDeleteError):
            await repo.delete_model('active-no-del')

    async def test_list_models_filter_by_provider(self, session: AsyncSession) -> None:
        repo = ModelConfigRepository(session)
        await repo.seed_defaults()
        await session.commit()

        claude_models = await repo.list_models(provider='claude')
        assert all(m.provider == 'claude' for m in claude_models)
        assert len(claude_models) == 3

        gemini_models = await repo.list_models(provider='gemini')
        assert all(m.provider == 'gemini' for m in gemini_models)
        assert len(gemini_models) == 2
