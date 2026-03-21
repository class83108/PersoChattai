"""模型配置 Repository — asyncpg 實作。"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import asyncpg

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


def _row_to_model(row: dict[str, Any]) -> ModelConfig:
    pricing = row['pricing']
    if isinstance(pricing, str):
        pricing = json.loads(pricing)
    return ModelConfig(
        id=str(row['id']),
        provider=row['provider'],
        model_id=row['model_id'],
        display_name=row['display_name'],
        is_active=row['is_active'],
        pricing=pricing,
        created_at=row.get('created_at'),
        updated_at=row.get('updated_at'),
    )


class ModelConfigRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def seed_defaults(self) -> None:
        async with self._pool.acquire() as conn:
            count = await conn.fetchval('SELECT COUNT(*) FROM model_config')
            if count > 0:
                return

            for model_data in _DEFAULT_CLAUDE_MODELS + _DEFAULT_GEMINI_MODELS:
                await conn.fetchrow(
                    """
                    INSERT INTO model_config (provider, model_id, display_name, is_active, pricing)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    RETURNING *
                    """,
                    model_data['provider'],
                    model_data['model_id'],
                    model_data['display_name'],
                    model_data['is_active'],
                    json.dumps(model_data['pricing']),
                )

        total = len(_DEFAULT_CLAUDE_MODELS) + len(_DEFAULT_GEMINI_MODELS)
        logger.info('已 seed %d 筆預設模型配置', total)

    async def list_models(self, *, provider: str | None = None) -> list[ModelConfig]:
        async with self._pool.acquire() as conn:
            if provider is not None:
                rows = await conn.fetch(
                    'SELECT * FROM model_config WHERE provider = $1 ORDER BY created_at',
                    provider,
                )
            else:
                rows = await conn.fetch('SELECT * FROM model_config ORDER BY created_at')
            return [_row_to_model(r) for r in rows]

    async def get_model(self, model_id: str) -> ModelConfig | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM model_config WHERE model_id = $1',
                model_id,
            )
            if row is None:
                return None
            return _row_to_model(row)

    async def get_active_model(self, provider: str) -> ModelConfig | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM model_config WHERE provider = $1 AND is_active = TRUE',
                provider,
            )
            if row is None:
                return None
            return _row_to_model(row)

    async def set_active_model(self, *, provider: str, model_id: str) -> None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM model_config WHERE model_id = $1 AND provider = $2',
                model_id,
                provider,
            )
            if row is None:
                msg = f'模型 {model_id} 不存在'
                raise ModelNotFoundError(msg)

            async with conn.transaction():
                now = datetime.now(tz=UTC)
                await conn.execute(
                    'UPDATE model_config SET is_active = FALSE, updated_at = $1'
                    ' WHERE provider = $2 AND is_active = TRUE',
                    now,
                    provider,
                )
                await conn.execute(
                    'UPDATE model_config SET is_active = TRUE, updated_at = $1 WHERE model_id = $2',
                    now,
                    model_id,
                )

    async def create_model(self, model: ModelConfig) -> ModelConfig:
        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO model_config (provider, model_id, display_name, is_active, pricing)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    RETURNING *
                    """,
                    model.provider,
                    model.model_id,
                    model.display_name,
                    model.is_active,
                    json.dumps(model.pricing),
                )
            except asyncpg.UniqueViolationError as e:
                msg = f'模型 {model.model_id} 已存在'
                raise DuplicateModelError(msg) from e
            return _row_to_model(row)

    async def update_model(self, model_id: str, updates: dict[str, Any]) -> ModelConfig:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                'SELECT * FROM model_config WHERE model_id = $1',
                model_id,
            )
            if existing is None:
                msg = f'模型 {model_id} 不存在'
                raise ModelNotFoundError(msg)

            set_parts = ['updated_at = $1']
            params: list[Any] = [datetime.now(tz=UTC)]
            idx = 2

            if 'display_name' in updates:
                set_parts.append(f'display_name = ${idx}')
                params.append(updates['display_name'])
                idx += 1

            if 'pricing' in updates:
                set_parts.append(f'pricing = ${idx}::jsonb')
                params.append(json.dumps(updates['pricing']))
                idx += 1

            params.append(model_id)
            set_clause = ', '.join(set_parts)
            sql = f'UPDATE model_config SET {set_clause} WHERE model_id = ${idx} RETURNING *'
            row = await conn.fetchrow(sql, *params)
            return _row_to_model(row)

    async def delete_model(self, model_id: str) -> None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT is_active FROM model_config WHERE model_id = $1',
                model_id,
            )
            if row is None:
                msg = f'模型 {model_id} 不存在'
                raise ModelNotFoundError(msg)

            if row['is_active']:
                msg = f'無法刪除 active 模型 {model_id}'
                raise ActiveModelDeleteError(msg)

            await conn.execute(
                'DELETE FROM model_config WHERE model_id = $1',
                model_id,
            )
