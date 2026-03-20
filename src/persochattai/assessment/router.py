"""Assessment Service router。"""

from fastapi import APIRouter

router = APIRouter(prefix='/api/assessment', tags=['assessment'])


@router.get('/health')
async def assessment_health() -> dict[str, str]:
    return {'service': 'assessment', 'status': 'ok'}
