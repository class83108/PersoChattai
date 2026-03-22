### Requirement: App 入口點
系統 SHALL 提供 `__main__.py` 模組，支援 `python -m persochattai` 啟動 uvicorn server。

#### Scenario: 啟動 server
- **WHEN** 執行 `python -m persochattai`
- **THEN** 系統 SHALL 以 uvicorn 啟動 FastAPI app
- **AND** 預設監聽 `0.0.0.0:8000`
- **AND** debug 模式時啟用 reload

### Requirement: Lifespan 服務初始化
系統 SHALL 在 lifespan startup 階段初始化所有服務，shutdown 階段清理資源。

#### Scenario: Startup 初始化順序
- **WHEN** app 啟動
- **THEN** 系統 SHALL 依序執行：
  1. 初始化 DB connection pool
  2. Seed model config defaults
  3. 初始化 UsageMonitor 並載入歷史
  4. 初始化 ConversationManager（注入 repository、scenario_designer、gemini_client）
  5. 掛載 FastRTC WebRTC stream 至 `/api/conversation/rtc`
  6. 啟動 ContentScheduler
- **AND** 所有服務 SHALL 存入 `app.state`

#### Scenario: Shutdown 清理順序
- **WHEN** app 關閉
- **THEN** 系統 SHALL 依序執行：
  1. 關閉 ContentScheduler
  2. 關閉 DB connection pool

#### Scenario: ConversationManager 注入依賴
- **WHEN** 初始化 ConversationManager
- **THEN** 系統 SHALL 注入 ConversationRepository（使用 DB pool）
- **AND** 注入 scenario_designer callable
- **AND** 注入 gemini client（使用 settings.gemini_api_key）
- **AND** 注入 AssessmentService

### Requirement: FastRTC 掛載
系統 SHALL 在 lifespan 中將 FastRTC WebRTC stream 掛載至 app。

#### Scenario: WebRTC stream 可用
- **WHEN** app 啟動完成
- **THEN** `/api/conversation/rtc` 路徑 SHALL 可接受 WebRTC 連線
- **AND** 使用 GeminiHandler 處理音訊雙向流
