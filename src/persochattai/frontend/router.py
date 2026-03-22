"""Frontend page routes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=['frontend'])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'templates'
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get('/')
async def index() -> RedirectResponse:
    return RedirectResponse(url='/materials', status_code=302)


def _render(request: Request, template: str, context: dict[str, Any] | None = None) -> Any:
    ctx = context or {}
    return templates.TemplateResponse(request=request, name=template, context=ctx)


# --- Page routes ---


@router.get('/materials', response_class=HTMLResponse)
async def materials(request: Request) -> Any:
    return _render(request, 'pages/materials.html')


@router.get('/roleplay', response_class=HTMLResponse)
async def roleplay(request: Request) -> Any:
    return _render(request, 'pages/roleplay.html')


@router.get('/report', response_class=HTMLResponse)
async def report(request: Request) -> Any:
    return _render(request, 'pages/report.html')


# --- HTMX partial routes (materials) ---

_API_BASE = 'http://localhost:8000'


def _api_url(path: str, request: Request) -> str:
    base = str(request.base_url).rstrip('/')
    return f'{base}{path}'


@router.get('/materials/partials/card-list', response_class=HTMLResponse)
async def card_list_partial(
    request: Request,
    source_type: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Any:
    params: dict[str, Any] = {'limit': limit, 'offset': offset}
    if source_type:
        params['source_type'] = source_type
    if difficulty:
        params['difficulty'] = difficulty
    if tag:
        params['tag'] = tag
    if keyword:
        params['keyword'] = keyword

    cards: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(_api_url('/api/content/cards', request), params=params)
            if resp.status_code == 200:
                cards = resp.json()
    except httpx.HTTPError:
        logger.exception('Failed to fetch cards from API')

    return _render(
        request,
        'partials/card_list.html',
        {
            'cards': cards,
            'limit': limit,
            'offset': offset,
            'source_type': source_type or '',
            'difficulty': difficulty or '',
            'keyword': keyword or '',
        },
    )


@router.post('/materials/upload-pdf', response_class=HTMLResponse)
async def upload_pdf_partial(request: Request, file: UploadFile) -> Any:
    content = await file.read()
    cards: list[dict[str, Any]] = []
    error = ''

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                _api_url('/api/content/upload-pdf', request),
                files={
                    'file': (
                        file.filename or 'upload.pdf',
                        content,
                        file.content_type or 'application/pdf',
                    )
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                cards = data.get('cards', [])
            else:
                detail = resp.json().get('detail', '上傳失敗')
                error = detail
    except httpx.HTTPError:
        logger.exception('Failed to upload PDF')
        error = '上傳失敗，請稍後再試'

    return _render(request, 'partials/upload_result.html', {'cards': cards, 'error': error})


@router.post('/materials/free-topic', response_class=HTMLResponse)
async def free_topic_partial(request: Request) -> Any:
    body = await request.json()
    cards: list[dict[str, Any]] = []
    error = ''

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                _api_url('/api/content/free-topic', request),
                json=body,
            )
            if resp.status_code == 200:
                data = resp.json()
                card = data.get('card', data.get('cards', []))
                cards = card if isinstance(card, list) else [card]
            else:
                detail = resp.json().get('detail', '提交失敗')
                error = detail
    except httpx.HTTPError:
        logger.exception('Failed to submit free topic')
        error = '提交失敗，請稍後再試'

    return _render(request, 'partials/upload_result.html', {'cards': cards, 'error': error})


# --- HTMX partial routes (roleplay) ---


@router.get('/roleplay/partials/history', response_class=HTMLResponse)
async def conversation_history_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    conversations: list[dict[str, Any]] = []
    if user_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    _api_url(f'/api/conversation/history/{user_id}', request),
                )
                if resp.status_code == 200:
                    conversations = resp.json()
        except httpx.HTTPError:
            logger.exception('Failed to fetch conversation history')

    return _render(
        request,
        'partials/conversation_history.html',
        {'conversations': conversations},
    )


# --- HTMX partial routes (report) ---


@router.get('/report/partials/overview', response_class=HTMLResponse)
async def report_overview_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    progress: dict[str, Any] = {}
    if user_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    _api_url(f'/api/assessment/user/{user_id}/progress', request),
                )
                if resp.status_code == 200:
                    progress = resp.json()
        except httpx.HTTPError:
            logger.exception('Failed to fetch assessment progress')

    return _render(request, 'partials/ability_overview.html', {'progress': progress})


@router.get('/report/partials/history', response_class=HTMLResponse)
async def report_history_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    assessments: list[dict[str, Any]] = []
    if user_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    _api_url(f'/api/assessment/user/{user_id}/history', request),
                )
                if resp.status_code == 200:
                    assessments = resp.json()
        except httpx.HTTPError:
            logger.exception('Failed to fetch assessment history')

    return _render(request, 'partials/assessment_history.html', {'assessments': assessments})


@router.get('/report/partials/vocabulary', response_class=HTMLResponse)
async def report_vocabulary_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    vocab: dict[str, Any] = {}
    if user_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    _api_url(f'/api/assessment/user/{user_id}/vocabulary', request),
                )
                if resp.status_code == 200:
                    vocab = resp.json()
        except httpx.HTTPError:
            logger.exception('Failed to fetch vocabulary stats')

    return _render(request, 'partials/vocabulary_stats.html', {'vocab': vocab})


@router.get('/report/partials/usage', response_class=HTMLResponse)
async def report_usage_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    usage: dict[str, Any] = {}
    if user_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    _api_url('/api/usage', request),
                    params={'user_id': user_id} if user_id else {},
                )
                if resp.status_code == 200:
                    usage = resp.json()
        except httpx.HTTPError:
            logger.exception('Failed to fetch usage stats')

    return _render(request, 'partials/usage_summary.html', {'usage': usage})
