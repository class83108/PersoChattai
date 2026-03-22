"""Conversation Service router。"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from persochattai.conversation.schemas import StartConversationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/conversation', tags=['conversation'])


def _get_manager(request: Request) -> Any:
    return request.app.state.conversation_manager


@router.get('/health')
async def conversation_health() -> dict[str, str]:
    return {'service': 'conversation', 'status': 'ok'}


@router.post('/start', status_code=201)
async def start_conversation(body: StartConversationRequest, request: Request) -> dict[str, Any]:
    manager = _get_manager(request)

    # Verify user exists
    user_repo = getattr(request.app.state, 'user_repository', None)
    if user_repo:
        user = await user_repo.get_by_id(body.user_id)
        if not user:
            raise HTTPException(status_code=404, detail='使用者不存在，請先建立帳號')

    has_active = await manager.has_active_conversation(body.user_id)
    if has_active:
        raise HTTPException(status_code=409, detail='使用者已有進行中的對話')

    try:
        return await manager.start_conversation(
            body.user_id, body.source_type.value, body.source_ref
        )
    except Exception as exc:
        logger.exception('建立對話失敗')
        raise HTTPException(status_code=500, detail='建立對話失敗') from exc


@router.get('/history/{user_id}')
async def get_history(user_id: uuid.UUID, request: Request) -> list[dict[str, Any]]:
    manager = _get_manager(request)
    return await manager.get_history(str(user_id))


@router.get('/{conversation_id}')
async def get_conversation(conversation_id: uuid.UUID, request: Request) -> dict[str, Any]:
    manager = _get_manager(request)
    state = await manager.get_state(str(conversation_id))
    if state is None:
        raise HTTPException(status_code=404, detail='對話不存在')
    return state


@router.post('/{conversation_id}/end')
async def end_conversation(conversation_id: uuid.UUID, request: Request) -> dict[str, Any]:
    manager = _get_manager(request)

    state = await manager.get_state(str(conversation_id))
    if state is None:
        raise HTTPException(status_code=404, detail='對話不存在')
    if state['status'] != 'active':
        raise HTTPException(status_code=409, detail='對話非 active 狀態')

    return await manager.end_conversation(str(conversation_id))


@router.post('/{conversation_id}/cancel')
async def cancel_conversation(conversation_id: uuid.UUID, request: Request) -> dict[str, Any]:
    manager = _get_manager(request)

    state = await manager.get_state(str(conversation_id))
    if state is None:
        raise HTTPException(status_code=404, detail='對話不存在')

    if state['status'] in ('completed', 'failed', 'cancelled'):
        raise HTTPException(status_code=409, detail=f'對話已 {state["status"]}，無法取消')

    return await manager.cancel_conversation(str(conversation_id))
