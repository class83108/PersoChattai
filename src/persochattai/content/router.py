"""Content Service router。"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile

from persochattai.content.schemas import FreeTopicRequest
from persochattai.content.service import ContentService, ContentServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/content', tags=['content'])

_MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB
_MAX_TEXT_CHARS = 5000


@router.get('/health')
async def content_health() -> dict[str, str]:
    return {'service': 'content', 'status': 'ok'}


@router.get('/cards')
async def list_cards(
    request: Request,
    source_type: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    repo = request.app.state.card_repository
    return await repo.list_cards(
        source_type=source_type,
        difficulty=difficulty,
        tag=tag,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )


@router.get('/cards/{card_id}')
async def get_card(request: Request, card_id: str) -> dict[str, Any]:
    repo = request.app.state.card_repository
    card = await repo.get_by_id(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail='卡片不存在')
    return card


@router.post('/upload-pdf')
async def upload_pdf(request: Request, file: UploadFile) -> dict[str, Any]:
    content = await file.read()
    if len(content) > _MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail='檔案過大，請上傳 10MB 以下的 PDF')

    try:
        text = ContentService.parse_pdf(content)
    except ContentServiceError as e:
        raise HTTPException(
            status_code=422,
            detail='無法讀取此 PDF，請確認檔案包含文字內容（非純圖片）',
        ) from e

    if not text:
        raise HTTPException(
            status_code=422,
            detail='無法讀取此 PDF，請確認檔案包含文字內容（非純圖片）',
        )

    truncated_text, was_truncated = ContentService.process_text(text, _MAX_TEXT_CHARS)

    service: ContentService = request.app.state.content_service
    cards = await service.summarize_pdf(truncated_text)

    return {'cards': cards, 'truncated': was_truncated}


@router.post('/free-topic')
async def free_topic(request: Request, body: FreeTopicRequest) -> dict[str, Any]:
    service: ContentService = request.app.state.content_service
    try:
        cards = await service.summarize_free_topic(body.topic)
    except ContentServiceError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {'card': cards[0] if len(cards) == 1 else cards}
