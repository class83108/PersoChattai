"""BYOA Core Agent factory。

建立共用的 Provider、UsageMonitor，以及各 Service 專用的 Agent 實例。
"""

from __future__ import annotations

from agent_core.agent import Agent
from agent_core.config import AgentCoreConfig, ProviderConfig
from agent_core.providers.anthropic_provider import AnthropicProvider
from agent_core.skills.base import Skill
from agent_core.skills.registry import SkillRegistry
from agent_core.tools.registry import ToolRegistry
from agent_core.usage_monitor import UsageMonitor

from persochattai.assessment.schemas import AssessmentServiceProtocol
from persochattai.config import Settings
from persochattai.content.schemas import CardRepositoryProtocol
from persochattai.tools import (
    build_assessment_tool_registry,
    build_content_tool_registry,
    build_conversation_tool_registry,
)

_provider: AnthropicProvider | None = None
_usage_monitor: UsageMonitor | None = None


def _get_provider(settings: Settings) -> AnthropicProvider:
    global _provider
    if _provider is None:
        config = ProviderConfig(
            provider_type='anthropic',
            api_key=settings.anthropic_api_key,
        )
        _provider = AnthropicProvider(config)
    return _provider


def _get_usage_monitor() -> UsageMonitor:
    global _usage_monitor
    if _usage_monitor is None:
        _usage_monitor = UsageMonitor()
    return _usage_monitor


def get_usage_monitor() -> UsageMonitor:
    return _get_usage_monitor()


# --- Skills ---

CONTENT_SUMMARIZER = Skill(
    name='content_summarizer',
    description='將 podcast 文字內容或 PDF 摘要成結構化學習卡片',
    instructions=(
        '你是一個英文學習內容摘要專家。收到原始文字內容後：\n'
        '1. 判斷內容是否適合拆成多張卡片（不同主題/對話情境）\n'
        '2. 對每張卡片使用 create_card tool 建立\n'
        '3. 每張卡片需包含：title, summary(3-5句), keywords(含定義和例句), '
        'dialogue_snippets(如有), difficulty_level(CEFR), tags\n'
        '4. difficulty_level 根據詞彙和句型複雜度判斷 CEFR 等級（A1-C2）'
    ),
)

SCENARIO_DESIGNER = Skill(
    name='scenario_designer',
    description='根據學習素材和使用者能力等級設計 Role Play 對話情境',
    instructions=(
        '你是一個英文 Role Play 情境設計師。根據提供的素材和使用者能力：\n'
        '1. 使用 query_cards 取得相關素材\n'
        '2. 使用 get_user_history 了解使用者能力等級\n'
        '3. 設計一個適合使用者等級的對話情境\n'
        '4. 輸出 JSON 格式的 system instruction，包含：\n'
        '   - role: 對話角色設定\n'
        '   - scenario: 情境描述\n'
        '   - objectives: 對話目標\n'
        '   - target_vocabulary: 目標詞彙\n'
        '   - difficulty: CEFR 等級'
    ),
)

TRANSCRIPT_EVALUATOR = Skill(
    name='transcript_evaluator',
    description='分析對話 transcript 並評估使用者英文能力',
    instructions=(
        '你是一個英文能力評估專家。收到 transcript 和 NLP 量化指標後：\n'
        '1. 使用 get_user_history 參考歷史評估\n'
        '2. 根據三個維度評估：Lexical Resource, Fluency & Coherence, '
        'Grammatical Range & Accuracy\n'
        '3. 判斷 CEFR 等級（A1-C2）\n'
        '4. 輸出 JSON 格式包含：\n'
        '   - cefr_level, lexical_assessment, fluency_assessment, grammar_assessment\n'
        '   - suggestions: 具體改善建議\n'
        '   - new_words: 本次對話中使用者使用的值得追蹤的詞彙列表'
    ),
)


def _build_agent(
    settings: Settings,
    system_prompt: str,
    skills: list[Skill],
    tool_registry: ToolRegistry | None = None,
) -> Agent:
    provider = _get_provider(settings)
    usage_monitor = _get_usage_monitor()

    skill_registry = SkillRegistry()
    for skill in skills:
        skill_registry.register(skill)

    config = AgentCoreConfig(
        provider=ProviderConfig(
            provider_type='anthropic',
            api_key=settings.anthropic_api_key,
        ),
        system_prompt=system_prompt,
    )

    return Agent(
        config=config,
        provider=provider,
        tool_registry=tool_registry,
        skill_registry=skill_registry,
        usage_monitor=usage_monitor,
    )


def create_content_agent(
    settings: Settings,
    card_repo: CardRepositoryProtocol,
) -> Agent:
    return _build_agent(
        settings=settings,
        system_prompt='你是英文學習內容摘要助手。使用繁體中文回應。',
        skills=[CONTENT_SUMMARIZER],
        tool_registry=build_content_tool_registry(card_repo),
    )


def create_conversation_agent(
    settings: Settings,
    card_repo: CardRepositoryProtocol,
    assessment_service: AssessmentServiceProtocol,
) -> Agent:
    return _build_agent(
        settings=settings,
        system_prompt='你是英文 Role Play 情境設計助手。使用繁體中文回應。',
        skills=[SCENARIO_DESIGNER],
        tool_registry=build_conversation_tool_registry(card_repo, assessment_service),
    )


def create_assessment_agent(
    settings: Settings,
    assessment_service: AssessmentServiceProtocol,
) -> Agent:
    return _build_agent(
        settings=settings,
        system_prompt='你是英文能力評估助手。使用繁體中文回應。',
        skills=[TRANSCRIPT_EVALUATOR],
        tool_registry=build_assessment_tool_registry(assessment_service),
    )
