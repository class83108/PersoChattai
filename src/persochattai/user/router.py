"""User identity router。"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

router = APIRouter(prefix='/api/users', tags=['users'])


class CreateUserRequest(BaseModel):
    display_name: str

    @field_validator('display_name', mode='before')
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            msg = 'display_name 不可為空'
            raise ValueError(msg)
        if len(v) > 20:
            msg = 'display_name 不可超過 20 字'
            raise ValueError(msg)
        return v


def _post_response(user: dict[str, Any]) -> dict[str, str]:
    return {'id': user['id'], 'display_name': user['display_name']}


@router.post('')
async def create_or_get_user(request: Request, body: CreateUserRequest) -> Any:
    repo = request.app.state.user_repository

    existing = await repo.get_by_display_name(body.display_name)
    if existing:
        return _post_response(existing)

    user = await repo.create(body.display_name)
    from starlette.responses import JSONResponse

    return JSONResponse(content=_post_response(user), status_code=201)


@router.get('/{user_id}')
async def get_user(request: Request, user_id: str) -> Any:
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail='user_id 格式不合法') from None

    repo = request.app.state.user_repository
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='使用者不存在')
    return user
