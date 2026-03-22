"""模型配置 Repository — SQLAlchemy 實作。"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import ModelConfigTable
from persochattai.usage.schemas import ModelConfig

logger = logging.getLogger(__name__)


class DuplicateModelError(Exception):
    pass


class ActiveModelDeleteError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


# 預設 seed 資料
_DEFAULT_CLAUDE_MODELS: list[dict[str, Any]] = [
    {
        'provider': 'claude',
        'model_id': 'claude-sonnet-4-20250514',
        'display_name': 'Claude Sonnet 4',
        'is_active': True,
        'pricing': {'input': 3.0, 'output': 15.0, 'cache_write': 3.75, 'cache_read': 0.30},
    },
    {
        'provider': 'claude',
        'model_id': 'claude-opus-4-20250514',
        'display_name': 'Claude Opus 4',
        'is_active': False,
        'pricing': {'input': 5.0, 'output': 25.0, 'cache_write': 6.25, 'cache_read': 0.50},
    },
    {
        'provider': 'claude',
        'model_id': 'claude-haiku-4-20250514',
        'display_name': 'Claude Haiku 4',
        'is_active': False,
        'pricing': {'input': 1.0, 'output': 5.0, 'cache_write': 1.25, 'cache_read': 0.10},
    },
]

_DEFAULT_GEMINI_MODELS: list[dict[str, Any]] = [
    {
        'provider': 'gemini',
        'model_id': 'gemini-2.0-flash',
        'display_name': 'Gemini 2.0 Flash',
        'is_active': True,
        'pricing': {'text_input': 0.10, 'audio_input': 0.70, 'output': 0.40, 'tokens_per_sec': 25},
    },
    {
        'provider': 'gemini',
        'model_id': 'gemini-2.5-flash',
        'display_name': 'Gemini 2.5 Flash',
        'is_active': False,
        'pricing': {'text_input': 0.30, 'audio_input': 1.00, 'output': 2.50, 'tokens_per_sec': 25},
    },
]


def _row_to_model(row: ModelConfigTable) -> ModelConfig:
    pricing = row.pricing
    if isinstance(pricing, str):
        pricing = json.loads(pricing)
    return ModelConfig(
        id=str(row.id),
        provider=row.provider,
        model_id=row.model_id,
        display_name=row.display_name,
        is_active=row.is_active,
        pricing=pricing,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ModelConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed_defaults(self) -> None:
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(ModelConfigTable)
        result = await self._session.execute(count_stmt)
        count = result.scalar() or 0
        if count > 0:
            return

        for model_data in _DEFAULT_CLAUDE_MODELS + _DEFAULT_GEMINI_MODELS:
            row = ModelConfigTable(
                provider=model_data['provider'],
                model_id=model_data['model_id'],
                display_name=model_data['display_name'],
                is_active=model_data['is_active'],
                pricing=model_data['pricing'],
            )
            self._session.add(row)
        await self._session.flush()

        total = len(_DEFAULT_CLAUDE_MODELS) + len(_DEFAULT_GEMINI_MODELS)
        logger.info('已 seed %d 筆預設模型配置', total)

    async def list_models(self, *, provider: str | None = None) -> list[ModelConfig]:
        stmt = select(ModelConfigTable).order_by(ModelConfigTable.created_at)
        if provider is not None:
            stmt = stmt.where(ModelConfigTable.provider == provider)
        result = await self._session.execute(stmt)
        return [_row_to_model(r) for r in result.scalars().all()]

    async def get_model(self, model_id: str) -> ModelConfig | None:
        stmt = select(ModelConfigTable).where(ModelConfigTable.model_id == model_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_model(row) if row else None

    async def get_active_model(self, provider: str) -> ModelConfig | None:
        stmt = select(ModelConfigTable).where(
            ModelConfigTable.provider == provider,
            ModelConfigTable.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_model(row) if row else None

    async def set_active_model(self, *, provider: str, model_id: str) -> None:
        # Check exists
        check_stmt = select(ModelConfigTable).where(
            ModelConfigTable.model_id == model_id,
            ModelConfigTable.provider == provider,
        )
        result = await self._session.execute(check_stmt)
        if result.scalar_one_or_none() is None:
            msg = f'模型 {model_id} 不存在'
            raise ModelNotFoundError(msg)

        now = datetime.now(tz=UTC)
        # Deactivate current
        deactivate = (
            update(ModelConfigTable)
            .where(ModelConfigTable.provider == provider, ModelConfigTable.is_active.is_(True))
            .values(is_active=False, updated_at=now)
        )
        await self._session.execute(deactivate)

        # Activate new
        activate = (
            update(ModelConfigTable)
            .where(ModelConfigTable.model_id == model_id)
            .values(is_active=True, updated_at=now)
        )
        await self._session.execute(activate)
        await self._session.flush()

    async def create_model(self, model: ModelConfig) -> ModelConfig:
        row = ModelConfigTable(
            provider=model.provider,
            model_id=model.model_id,
            display_name=model.display_name,
            is_active=model.is_active,
            pricing=model.pricing,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            msg = f'模型 {model.model_id} 已存在'
            raise DuplicateModelError(msg) from e
        return _row_to_model(row)

    async def update_model(self, model_id: str, updates: dict[str, Any]) -> ModelConfig:
        stmt = select(ModelConfigTable).where(ModelConfigTable.model_id == model_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            msg = f'模型 {model_id} 不存在'
            raise ModelNotFoundError(msg)

        if 'display_name' in updates:
            row.display_name = updates['display_name']
        if 'pricing' in updates:
            row.pricing = updates['pricing']
        row.updated_at = datetime.now(tz=UTC)
        await self._session.flush()
        return _row_to_model(row)

    async def delete_model(self, model_id: str) -> None:
        stmt = select(ModelConfigTable).where(ModelConfigTable.model_id == model_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            msg = f'模型 {model_id} 不存在'
            raise ModelNotFoundError(msg)
        if row.is_active:
            msg = f'無法刪除 active 模型 {model_id}'
            raise ActiveModelDeleteError(msg)

        del_stmt = delete(ModelConfigTable).where(ModelConfigTable.model_id == model_id)
        await self._session.execute(del_stmt)
        await self._session.flush()
