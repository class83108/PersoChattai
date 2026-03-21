## ADDED Requirements

### Requirement: Claude Provider 共用實例
系統 SHALL 建立共用的 AnthropicProvider 實例，供所有 Service 的 Agent 使用。

#### Scenario: Provider 使用環境變數中的 API key
- **WHEN** 建立 AnthropicProvider
- **THEN** 使用 Settings.anthropic_api_key 初始化

#### Scenario: Provider 共用 UsageMonitor
- **WHEN** 多個 Agent 使用同一個 Provider
- **THEN** 所有 API 呼叫的用量記錄彙總在同一個 UsageMonitor

### Requirement: Agent factory per Service
系統 SHALL 為每個 Service 提供專用的 Agent factory function。

#### Scenario: Content Agent factory
- **WHEN** 呼叫 create_content_agent()
- **THEN** 回傳配置了 content_summarizer skill 和 create_card / query_cards tools 的 Agent 實例

#### Scenario: Conversation Agent factory
- **WHEN** 呼叫 create_conversation_agent()
- **THEN** 回傳配置了 scenario_designer skill 和 query_cards / get_user_history tools 的 Agent 實例

#### Scenario: Assessment Agent factory
- **WHEN** 呼叫 create_assessment_agent()
- **THEN** 回傳配置了 transcript_evaluator skill 和 get_user_history tool 的 Agent 實例

### Requirement: UsageMonitor API 用量查詢
系統 SHALL 提供 endpoint 查詢 API 使用量。

#### Scenario: 查詢用量摘要
- **WHEN** GET /api/usage
- **THEN** 回傳 UsageMonitor.get_summary() 的 JSON 結果，包含 token 用量與費用估算
