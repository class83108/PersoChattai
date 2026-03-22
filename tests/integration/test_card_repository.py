"""CardRepository 整合測試 — 接真實 PostgreSQL。"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.content.repository import CardRepository


@pytest.mark.asyncio
class TestCardRepositoryIntegration:
    async def test_create_and_get_by_id(self, session: AsyncSession) -> None:
        repo = CardRepository(session)
        card = await repo.create(
            {
                'source_type': 'podcast',
                'source_url': 'https://example.com/ep1',
                'title': 'Test Episode',
                'summary': 'A test episode summary',
                'keywords': ['test', 'episode'],
                'tags': ['beginner'],
            }
        )
        await session.commit()

        assert card['title'] == 'Test Episode'
        assert card['source_type'] == 'podcast'

        fetched = await repo.get_by_id(str(card['id']))
        assert fetched is not None
        assert fetched['title'] == 'Test Episode'
        assert fetched['keywords'] == ['test', 'episode']
        assert fetched['tags'] == ['beginner']

    async def test_upsert_duplicate_url_returns_empty(self, session: AsyncSession) -> None:
        repo = CardRepository(session)
        url = 'https://example.com/dup'

        first = await repo.create(
            {
                'source_type': 'podcast',
                'source_url': url,
                'title': 'First',
                'summary': 'First summary',
            }
        )
        await session.commit()
        assert first != {}

        # 同一 URL 不會建立新 card
        second = await repo.create(
            {
                'source_type': 'podcast',
                'source_url': url,
                'title': 'Second',
                'summary': 'Second summary',
            }
        )
        assert second == {}

    async def test_create_without_url_allows_duplicates(self, session: AsyncSession) -> None:
        repo = CardRepository(session)
        first = await repo.create(
            {
                'source_type': 'free_topic',
                'title': 'Topic A',
                'summary': 'Summary A',
            }
        )
        second = await repo.create(
            {
                'source_type': 'free_topic',
                'title': 'Topic B',
                'summary': 'Summary B',
            }
        )
        await session.commit()
        assert first != {}
        assert second != {}

    async def test_exists_by_url(self, session: AsyncSession) -> None:
        repo = CardRepository(session)
        url = 'https://example.com/exists'

        assert await repo.exists_by_url(url) is False

        await repo.create(
            {
                'source_type': 'bbc',
                'source_url': url,
                'title': 'Exists Test',
                'summary': 'Summary',
            }
        )
        await session.commit()

        assert await repo.exists_by_url(url) is True

    async def test_list_cards_with_filters(self, session: AsyncSession) -> None:
        repo = CardRepository(session)

        for i in range(3):
            await repo.create(
                {
                    'source_type': 'podcast',
                    'source_url': f'https://example.com/filter-{i}',
                    'title': f'Podcast {i}',
                    'summary': f'Summary {i}',
                    'difficulty_level': 'B1' if i < 2 else 'C1',
                    'tags': ['english'] if i == 0 else ['test'],
                }
            )
        await session.commit()

        # filter by source_type
        all_podcasts = await repo.list_cards(source_type='podcast')
        assert len(all_podcasts) >= 3

        # filter by difficulty
        b1_cards = await repo.list_cards(difficulty='B1')
        assert all(c['difficulty_level'] == 'B1' for c in b1_cards)

        # filter by tag
        english_cards = await repo.list_cards(tag='english')
        assert len(english_cards) >= 1

        # filter by keyword
        keyword_cards = await repo.list_cards(keyword='Podcast 0')
        assert len(keyword_cards) >= 1

        # pagination
        page = await repo.list_cards(source_type='podcast', limit=2, offset=0)
        assert len(page) <= 2
