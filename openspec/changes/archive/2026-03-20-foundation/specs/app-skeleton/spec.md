## ADDED Requirements

### Requirement: 環境變數配置
系統 SHALL 從 .env 檔案和環境變數讀取配置，缺少必要變數時阻止啟動。

#### Scenario: 所有必要變數存在
- **WHEN** .env 包含 DB_URL, ANTHROPIC_API_KEY, GEMINI_API_KEY
- **THEN** Settings 物件正確建立，所有欄位有值

#### Scenario: 缺少必要變數
- **WHEN** DB_URL 未設定
- **THEN** 系統 SHALL 拋出 ValueError 並明確指出缺少哪個變數

#### Scenario: 提供 .env.example 模板
- **WHEN** 開發者 clone 專案
- **THEN** 存在 .env.example 列出所有必要與可選的環境變數

### Requirement: FastAPI app factory
系統 SHALL 提供 create_app() factory function 建立 FastAPI 應用。

#### Scenario: 建立 app 實例
- **WHEN** 呼叫 create_app()
- **THEN** 回傳已掛載所有 router 的 FastAPI 實例

#### Scenario: Health check endpoint
- **WHEN** GET /health
- **THEN** 回傳 200 status 與 {"status": "ok"}

### Requirement: Router 掛載
系統 SHALL 掛載三大 Service 的 router。

#### Scenario: Content router 掛載
- **WHEN** app 啟動
- **THEN** /api/content/* 路徑可存取

#### Scenario: Conversation router 掛載
- **WHEN** app 啟動
- **THEN** /api/conversation/* 路徑可存取

#### Scenario: Assessment router 掛載
- **WHEN** app 啟動
- **THEN** /api/assessment/* 路徑可存取

### Requirement: Lifecycle 管理
FastAPI app SHALL 透過 lifespan 管理資源的建立與釋放。

#### Scenario: 啟動時初始化資源
- **WHEN** app 啟動
- **THEN** 依序建立 DB connection pool 並記錄 log

#### Scenario: 關閉時釋放資源
- **WHEN** app 關閉
- **THEN** 依序關閉 DB connection pool 並記錄 log
