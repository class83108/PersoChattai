"""Frontend page routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=['frontend'])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'templates'
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get('/')
async def index() -> RedirectResponse:
    return RedirectResponse(url='/materials', status_code=302)


def _render(request: Request, template: str) -> Any:
    return templates.TemplateResponse(request=request, name=template)


@router.get('/materials', response_class=HTMLResponse)
async def materials(request: Request) -> Any:
    return _render(request, 'pages/materials.html')


@router.get('/roleplay', response_class=HTMLResponse)
async def roleplay(request: Request) -> Any:
    return _render(request, 'pages/roleplay.html')


@router.get('/report', response_class=HTMLResponse)
async def report(request: Request) -> Any:
    return _render(request, 'pages/report.html')
