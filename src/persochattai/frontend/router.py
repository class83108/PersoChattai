"""Frontend page routes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

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


# --- Internal helpers ---


def _safe_path_segment(value: str) -> str:
    """Sanitise a user-supplied value before embedding it in a URL path.

    Rejects path traversal characters (/, ..) and encodes the rest.
    """
    stripped = value.strip()
    if not stripped or '/' in stripped or '..' in stripped:
        return ''
    return quote(stripped, safe='')


def _api_url(path: str, request: Request) -> str:
    """Build internal API URL from the app's own base URL.

    Uses scheme + server from the ASGI scope (not the Host header)
    to prevent host-header injection.
    """
    scope = request.scope
    scheme = scope.get('scheme', 'http')
    server = scope.get('server')
    if server:
        host, port = server
        base = f'{scheme}://{host}:{port}'
    else:
        base = f'{scheme}://127.0.0.1:8000'
    return f'{base}{path}'


def _parse_error_detail(resp: httpx.Response, fallback: str) -> str:
    """Safely extract error detail from a non-200 API response."""
    try:
        return resp.json().get('detail', fallback)
    except (json.JSONDecodeError, ValueError):
        return fallback


async def _proxy_get(
    request: Request,
    api_path: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    """GET proxy to internal API. Returns parsed JSON or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_api_url(api_path, request), params=params)
            if resp.status_code == 200:
                return resp.json()
            logger.warning('API %s returned %s', api_path, resp.status_code)
    except httpx.HTTPError:
        logger.exception('Failed to fetch %s', api_path)
    return None


async def _proxy_get_for_user(
    request: Request,
    api_path: str,
    user_id: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    """GET proxy with user_id sanitisation. Returns parsed JSON or None."""
    safe_uid = _safe_path_segment(user_id)
    if not safe_uid:
        return None
    path = api_path.format(user_id=safe_uid)
    return await _proxy_get(request, path, params=params)


# --- HTMX partial routes (materials) ---


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

    cards = await _proxy_get(request, '/api/content/cards', params=params) or []

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
                error = _parse_error_detail(resp, '上傳失敗')
    except httpx.HTTPError:
        logger.exception('Failed to upload PDF')
        error = '上傳失敗，請稍後再試'

    return _render(request, 'partials/upload_result.html', {'cards': cards, 'error': error})


@router.post('/materials/free-topic', response_class=HTMLResponse)
async def free_topic_partial(request: Request) -> Any:
    form = await request.form()
    body = dict(form)
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
                error = _parse_error_detail(resp, '提交失敗')
    except httpx.HTTPError:
        logger.exception('Failed to submit free topic')
        error = '提交失敗，請稍後再試'

    return _render(request, 'partials/upload_result.html', {'cards': cards, 'error': error})


@router.post('/materials/trigger-crawl', response_class=HTMLResponse)
async def trigger_crawl_partial(request: Request) -> Any:
    error = ''
    result: dict[str, Any] = {}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(_api_url('/api/content/trigger-crawl', request))
            if resp.status_code == 200:
                result = resp.json()
            elif resp.status_code == 409:
                error = _parse_error_detail(resp, '爬蟲正在執行中，請稍後再試')
            else:
                error = _parse_error_detail(resp, '爬取失敗')
    except httpx.HTTPError:
        logger.exception('Failed to trigger crawl')
        error = '爬取失敗，請稍後再試'

    return _render(
        request,
        'partials/crawl_result.html',
        {
            'error': error,
            'total_new': result.get('total_new', 0),
            'total_skipped': result.get('total_skipped', 0),
            'total_failed': result.get('total_failed', 0),
            'sources': result.get('sources', []),
        },
    )


# --- HTMX partial routes (roleplay) ---


@router.get('/roleplay/partials/card-picker', response_class=HTMLResponse)
async def card_picker_partial(request: Request) -> Any:
    cards = await _proxy_get(request, '/api/content/cards', params={'limit': 50}) or []
    return _render(request, 'partials/card_picker.html', {'cards': cards})


@router.get('/roleplay/partials/history', response_class=HTMLResponse)
async def conversation_history_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    conversations = (
        await _proxy_get_for_user(request, '/api/conversation/history/{user_id}', user_id) or []
    )
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
    progress = (
        await _proxy_get_for_user(request, '/api/assessment/user/{user_id}/progress', user_id) or {}
    )
    return _render(request, 'partials/ability_overview.html', {'progress': progress})


@router.get('/report/partials/history', response_class=HTMLResponse)
async def report_history_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    assessments = (
        await _proxy_get_for_user(request, '/api/assessment/user/{user_id}/history', user_id) or []
    )
    return _render(request, 'partials/assessment_history.html', {'assessments': assessments})


@router.get('/report/partials/vocabulary', response_class=HTMLResponse)
async def report_vocabulary_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    vocab = (
        await _proxy_get_for_user(request, '/api/assessment/user/{user_id}/vocabulary', user_id)
        or {}
    )
    return _render(request, 'partials/vocabulary_stats.html', {'vocab': vocab})


@router.get('/report/partials/usage', response_class=HTMLResponse)
async def report_usage_partial(
    request: Request,
    user_id: str = '',
) -> Any:
    safe_uid = _safe_path_segment(user_id)
    usage = (
        await _proxy_get(request, '/api/usage', params={'user_id': safe_uid}) if safe_uid else None
    ) or {}
    return _render(request, 'partials/usage_summary.html', {'usage': usage})
