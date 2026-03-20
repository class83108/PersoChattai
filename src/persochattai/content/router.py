"""Content Service router。"""

from fastapi import APIRouter

router = APIRouter(prefix='/api/content', tags=['content'])


@router.get('/health')
async def content_health() -> dict[str, str]:
    return {'service': 'content', 'status': 'ok'}
