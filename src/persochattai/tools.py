"""BYOA Tools — tool handlers 與 registry 組裝。"""

from __future__ import annotations

from typing import Any

from agent_core.tools.registry import ToolRegistry

from persochattai.assessment.schemas import AssessmentServiceProtocol
from persochattai.content.schemas import CardRepositoryProtocol

# --- Tool Handlers (closure factories) ---

_REQUIRED_CARD_FIELDS = ('title', 'summary', 'keywords', 'source_type', 'difficulty_level')


def create_query_cards_handler(
    card_repo: CardRepositoryProtocol,
) -> Any:
    async def query_cards(
        source_type: str | None = None,
        difficulty_level: str | None = None,
        tag: str | None = None,
        keyword: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await card_repo.list_cards(
            source_type=source_type,
            difficulty=difficulty_level,
            tag=tag,
            keyword=keyword,
            limit=limit,
        )

    return query_cards


def create_create_card_handler(
    card_repo: CardRepositoryProtocol,
) -> Any:
    async def create_card(**kwargs: Any) -> dict[str, Any]:
        missing = [f for f in _REQUIRED_CARD_FIELDS if not kwargs.get(f)]
        if missing:
            return {'error': f'缺少必填欄位: {", ".join(missing)}'}
        return await card_repo.create(kwargs)

    return create_card


def create_get_user_history_handler(
    assessment_service: AssessmentServiceProtocol,
) -> Any:
    async def get_user_history(user_id: str) -> dict[str, Any]:
        return await assessment_service.get_user_history(user_id)

    return get_user_history


# --- JSON Schema definitions for BYOA ToolRegistry ---

_QUERY_CARDS_PARAMS = {
    'type': 'object',
    'properties': {
        'source_type': {'type': 'string', 'description': '來源類型篩選'},
        'difficulty_level': {'type': 'string', 'description': 'CEFR 等級篩選'},
        'tag': {'type': 'string', 'description': 'Tag 篩選（單一值）'},
        'keyword': {'type': 'string', 'description': '關鍵字搜尋'},
        'limit': {'type': 'integer', 'default': 10, 'description': '回傳上限'},
    },
}

_CREATE_CARD_PARAMS = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string', 'description': '卡片標題'},
        'summary': {'type': 'string', 'description': '摘要 (3-5 句)'},
        'keywords': {
            'type': 'array',
            'items': {'type': 'object'},
            'description': '關鍵詞彙 [{word, definition, example}]',
        },
        'source_type': {'type': 'string', 'description': '來源類型'},
        'source_url': {'type': 'string', 'description': '來源 URL'},
        'dialogue_snippets': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': '對話片段',
        },
        'difficulty_level': {'type': 'string', 'description': 'CEFR 等級'},
        'tags': {'type': 'array', 'items': {'type': 'string'}, 'description': '標籤'},
    },
    'required': ['title', 'summary', 'keywords', 'source_type', 'difficulty_level'],
}

_GET_USER_HISTORY_PARAMS = {
    'type': 'object',
    'properties': {
        'user_id': {'type': 'string', 'description': '使用者 ID'},
    },
    'required': ['user_id'],
}


# --- Registry builders ---


def build_content_tool_registry(
    card_repo: CardRepositoryProtocol,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name='create_card',
        description='建立學習卡片',
        parameters=_CREATE_CARD_PARAMS,
        handler=create_create_card_handler(card_repo),
    )
    return registry


def build_conversation_tool_registry(
    card_repo: CardRepositoryProtocol,
    assessment_service: AssessmentServiceProtocol,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name='query_cards',
        description='查詢素材卡片',
        parameters=_QUERY_CARDS_PARAMS,
        handler=create_query_cards_handler(card_repo),
    )
    registry.register(
        name='get_user_history',
        description='查詢使用者能力歷史',
        parameters=_GET_USER_HISTORY_PARAMS,
        handler=create_get_user_history_handler(assessment_service),
    )
    return registry


def build_assessment_tool_registry(
    assessment_service: AssessmentServiceProtocol,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name='get_user_history',
        description='查詢使用者能力歷史',
        parameters=_GET_USER_HISTORY_PARAMS,
        handler=create_get_user_history_handler(assessment_service),
    )
    return registry
