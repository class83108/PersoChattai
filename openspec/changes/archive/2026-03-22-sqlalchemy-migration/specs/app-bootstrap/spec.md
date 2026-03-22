## MODIFIED Requirements

### Requirement: Lifespan 服務初始化
系統 SHALL 在 lifespan startup 階段初始化所有服務，shutdown 階段清理資源。

#### Scenario: Startup 初始化順序
- **WHEN** app 啟動
- **THEN** 系統 SHALL 依序執行：
  1. 建立 SQLAlchemy async engine 與 session factory
  2. 執行 Alembic migration 至最新版本
  3. Seed model config defaults
  4. 初始化 UsageMonitor 並載入歷史
  5. 初始化 ConversationManager（注入 repository、scenario_designer、gemini_client）
  6. 掛載 FastRTC WebRTC stream 至 `/api/conversation/rtc`
  7. 啟動 ContentScheduler
- **AND** 所有服務 SHALL 存入 `app.state`

#### Scenario: Shutdown 清理順序
- **WHEN** app 關閉
- **THEN** 系統 SHALL 依序執行：
  1. 關閉 ContentScheduler
  2. Dispose SQLAlchemy async engine

#### Scenario: ConversationManager 注入依賴
- **WHEN** 初始化 ConversationManager
- **THEN** 系統 SHALL 注入 ConversationRepository（使用 AsyncSession）
- **AND** 注入 scenario_designer callable
- **AND** 注入 gemini client（使用 settings.gemini_api_key）
- **AND** 注入 AssessmentService
