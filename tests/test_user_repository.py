"""UserRepository 單元測試（mock AsyncSession）。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from persochattai.database.tables import UserTable
from persochattai.user.repository import UserRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo(mock_session: AsyncMock) -> UserRepository:
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_create_returns_user_dict(repo: UserRepository, mock_session: AsyncMock) -> None:
    result = await repo.create('小明')

    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    assert result['display_name'] == '小明'
    uuid.UUID(result['id'])  # valid UUID


@pytest.mark.asyncio
async def test_get_by_id_found(repo: UserRepository, mock_session: AsyncMock) -> None:
    user_row = UserTable(id=uuid.uuid4(), display_name='小明', current_level='B1')
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = user_row
    mock_session.execute.return_value = execute_result

    result = await repo.get_by_id(str(user_row.id))

    assert result is not None
    assert result['display_name'] == '小明'
    assert result['current_level'] == 'B1'


@pytest.mark.asyncio
async def test_get_by_id_not_found(repo: UserRepository, mock_session: AsyncMock) -> None:
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = execute_result

    result = await repo.get_by_id(str(uuid.uuid4()))
    assert result is None


@pytest.mark.asyncio
async def test_get_by_display_name_found(repo: UserRepository, mock_session: AsyncMock) -> None:
    user_row = UserTable(id=uuid.uuid4(), display_name='小華', current_level=None)
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = user_row
    mock_session.execute.return_value = execute_result

    result = await repo.get_by_display_name('小華')

    assert result is not None
    assert result['display_name'] == '小華'
    assert result['current_level'] is None


@pytest.mark.asyncio
async def test_get_by_display_name_not_found(repo: UserRepository, mock_session: AsyncMock) -> None:
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = execute_result

    result = await repo.get_by_display_name('不存在')
    assert result is None
