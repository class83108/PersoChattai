"""模型配置與設定 API 端點。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from persochattai.usage.model_config_repository import (
    ActiveModelDeleteError,
    DuplicateModelError,
    ModelNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request / Response models ---


class CreateModelRequest(BaseModel):
    provider: str
    model_id: str
    display_name: str
    pricing: dict[str, Any]
    is_active: bool = False


class UpdateModelRequest(BaseModel):
    display_name: str | None = None
    pricing: dict[str, Any] | None = None


class UpdateSettingsRequest(BaseModel):
    claude_model: str | None = None
    gemini_model: str | None = None


# --- Helpers ---


def _get_model_repo(request: Request) -> Any:
    return request.app.state.model_config_repo


# --- /api/models ---


@router.get('/api/models')
async def list_models(request: Request, provider: str | None = None) -> list[dict[str, Any]]:
    repo = _get_model_repo(request)
    models = await repo.list_models(provider=provider)
    return [m.to_dict() for m in models]


@router.post('/api/models', status_code=201)
async def create_model(request: Request, body: CreateModelRequest) -> dict[str, Any]:
    from persochattai.usage.schemas import ModelConfig

    repo = _get_model_repo(request)
    model = ModelConfig(
        provider=body.provider,
        model_id=body.model_id,
        display_name=body.display_name,
        is_active=body.is_active,
        pricing=body.pricing,
    )
    try:
        created = await repo.create_model(model)
    except DuplicateModelError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return created.to_dict()


@router.put('/api/models/{model_id}')
async def update_model(request: Request, model_id: str, body: UpdateModelRequest) -> dict[str, Any]:
    repo = _get_model_repo(request)
    updates: dict[str, Any] = {}
    if body.display_name is not None:
        updates['display_name'] = body.display_name
    if body.pricing is not None:
        updates['pricing'] = body.pricing
    try:
        updated = await repo.update_model(model_id, updates)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return updated.to_dict()


@router.delete('/api/models/{model_id}', status_code=204)
async def delete_model(request: Request, model_id: str) -> None:
    repo = _get_model_repo(request)
    try:
        await repo.delete_model(model_id)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ActiveModelDeleteError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


# --- /api/settings ---


@router.get('/api/settings')
async def get_settings(request: Request) -> dict[str, Any]:
    repo = _get_model_repo(request)
    settings = request.app.state.settings

    claude_active = await repo.get_active_model('claude')
    gemini_active = await repo.get_active_model('gemini')

    claude_models = await repo.list_models(provider='claude')
    gemini_models = await repo.list_models(provider='gemini')

    return {
        'claude_model': claude_active.model_id if claude_active else settings.claude_model,
        'gemini_model': gemini_active.model_id if gemini_active else settings.gemini_model,
        'available_claude_models': [m.to_dict() for m in claude_models],
        'available_gemini_models': [m.to_dict() for m in gemini_models],
    }


@router.put('/api/settings')
async def update_settings(request: Request, body: UpdateSettingsRequest) -> dict[str, Any]:
    if body.claude_model is None and body.gemini_model is None:
        raise HTTPException(status_code=422, detail='至少需要提供 claude_model 或 gemini_model')

    repo = _get_model_repo(request)

    try:
        if body.claude_model is not None:
            await repo.set_active_model(provider='claude', model_id=body.claude_model)
        if body.gemini_model is not None:
            await repo.set_active_model(provider='gemini', model_id=body.gemini_model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return await get_settings(request)
