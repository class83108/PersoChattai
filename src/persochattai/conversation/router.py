"""Conversation Service router。"""

from fastapi import APIRouter

router = APIRouter(prefix='/api/conversation', tags=['conversation'])


@router.get('/health')
async def conversation_health() -> dict[str, str]:
    return {'service': 'conversation', 'status': 'ok'}
