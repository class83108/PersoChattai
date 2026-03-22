"""Conversation API — user_id 存在性驗證測試。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from persochattai.app import create_app
from persochattai.config import Settings


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock()
    manager.has_active_conversation = AsyncMock(return_value=False)
    manager.start_conversation = AsyncMock(
        return_value={'conversation_id': str(uuid.uuid4()), 'status': 'preparing'}
    )
    return manager


@pytest.fixture
def client(mock_manager: MagicMock, mock_user_repo: AsyncMock) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.conversation_manager = mock_manager
    app.state.user_repository = mock_user_repo
    return TestClient(app)


def test_start_conversation_user_not_found(client: TestClient, mock_user_repo: AsyncMock) -> None:
    mock_user_repo.get_by_id.return_value = None

    resp = client.post(
        '/api/conversation/start',
        json={
            'user_id': str(uuid.uuid4()),
            'source_type': 'card',
            'source_ref': 'card-123',
        },
    )

    assert resp.status_code == 404
    assert '使用者不存在' in resp.json()['detail']


def test_start_conversation_user_exists(
    client: TestClient, mock_user_repo: AsyncMock, mock_manager: MagicMock
) -> None:
    user_id = str(uuid.uuid4())
    mock_user_repo.get_by_id.return_value = {'id': user_id, 'display_name': 'test'}

    resp = client.post(
        '/api/conversation/start',
        json={
            'user_id': user_id,
            'source_type': 'card',
            'source_ref': 'card-123',
        },
    )

    assert resp.status_code == 201
    mock_manager.start_conversation.assert_awaited_once()
