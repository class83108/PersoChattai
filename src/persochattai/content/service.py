"""Content Service — 摘要 pipeline。"""

from __future__ import annotations

import io
import logging
from typing import Any

import pdfplumber

from persochattai.content.schemas import CardRepositoryProtocol
from persochattai.content.scraper.protocol import RawArticle

logger = logging.getLogger(__name__)

CEFR_LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}


class ContentServiceError(Exception):
    """Content Service 錯誤。"""


class ContentService:
    def __init__(self, repository: CardRepositoryProtocol, agent: Any) -> None:
        self._repo = repository
        self._agent = agent

    @staticmethod
    def truncate_text(text: str, max_chars: int = 5000) -> str:
        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]
        last_sentence = max(
            truncated.rfind('.'),
            truncated.rfind('?'),
            truncated.rfind('!'),
        )
        if last_sentence > 0:
            truncated = truncated[: last_sentence + 1]
        return truncated

    @staticmethod
    def process_text(text: str, max_chars: int = 5000) -> tuple[str, bool]:
        if len(text) <= max_chars:
            return text, False
        return ContentService.truncate_text(text, max_chars), True

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return '\n'.join(page.extract_text() or '' for page in pdf.pages).strip()
        except Exception as e:
            raise ContentServiceError('無法解析 PDF') from e

    async def summarize_article(
        self, article: RawArticle, source_type: str = 'podcast_allearsenglish'
    ) -> list[dict[str, Any]]:
        return await self._summarize_and_save(
            text=article.content,
            source_type=source_type,
            source_url=article.url,
            context_label=article.url,
        )

    async def summarize_pdf(self, text: str) -> list[dict[str, Any]]:
        return await self._summarize_and_save(
            text=text,
            source_type='user_pdf',
            context_label='PDF',
        )

    async def summarize_free_topic(self, topic: str) -> list[dict[str, Any]]:
        return await self._summarize_and_save(
            text=topic,
            source_type='user_prompt',
            context_label='free topic',
        )

    async def _summarize_and_save(
        self,
        text: str,
        source_type: str,
        source_url: str | None = None,
        context_label: str = '',
    ) -> list[dict[str, Any]]:
        try:
            result = await self._agent.run(text)
        except Exception as e:
            logger.error('Claude Agent 摘要失敗: %s', context_label)
            raise ContentServiceError('摘要失敗') from e

        cards = self._parse_agent_result(result)
        if not cards:
            logger.error('Claude Agent 回傳無法解析的格式: %s', context_label)
            raise ContentServiceError('摘要結果格式錯誤')

        self._validate_cards(cards)

        saved: list[dict[str, Any]] = []
        for card_data in cards:
            card_data['source_type'] = source_type
            if source_url:
                card_data['source_url'] = source_url
            result_card = await self._repo.create(card_data)
            saved.append(result_card)
        return saved

    def _parse_agent_result(self, result: Any) -> list[dict[str, Any]] | None:
        if isinstance(result, list):
            if all(isinstance(item, dict) for item in result):
                return result
            return None
        if isinstance(result, dict):
            return [result]
        return None

    def _validate_cards(self, cards: list[dict[str, Any]]) -> None:
        required = {'title', 'summary'}
        for card in cards:
            if not isinstance(card, dict) or not required.issubset(card.keys()):
                raise ContentServiceError('摘要結果格式錯誤：缺少必要欄位')
            dl = card.get('difficulty_level')
            if dl and dl not in CEFR_LEVELS:
                raise ContentServiceError(f'無效的 CEFR 等級: {dl}')
