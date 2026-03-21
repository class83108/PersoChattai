"""Assessment Service router。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix='/api/assessment', tags=['assessment'])


@router.get('/health')
async def assessment_health() -> dict[str, str]:
    return {'service': 'assessment', 'status': 'ok'}


@router.get('/user/{user_id}/history')
async def get_user_history(
    request: Request,
    user_id: str,
    limit: int = 10,
    offset: int = 0,
) -> list[dict[str, Any]]:
    repo = request.app.state.assessment_repo
    return await repo.list_by_user(user_id, limit=limit, offset=offset)


@router.get('/user/{user_id}/vocabulary')
async def get_user_vocabulary(request: Request, user_id: str) -> dict[str, Any]:
    repo = request.app.state.vocabulary_repo
    return await repo.get_vocabulary_stats(user_id)


@router.get('/user/{user_id}/progress')
async def get_user_progress(request: Request, user_id: str) -> dict[str, Any]:
    service = request.app.state.assessment_service
    return await service.get_user_history(user_id)


@router.get('/{assessment_id}')
async def get_assessment(request: Request, assessment_id: str) -> dict[str, Any]:
    repo = request.app.state.assessment_repo
    result = await repo.get_by_id(assessment_id)
    if result is None:
        raise HTTPException(status_code=404, detail='評估記錄不存在')
    return result
