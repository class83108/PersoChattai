## Why

PersoChattai 專案需要基礎架構才能開始開發任何功能。目前專案只有空的目錄結構和依賴配置，缺少 DB schema、FastAPI app 骨架、BYOA Core 整合、以及環境設定。這是所有後續功能（Content Service、Conversation Service、Assessment Service）的前置條件。

## What Changes

- 建立 PostgreSQL DB schema（users, cards, conversations, assessments, user_vocabulary, user_level_snapshots）
- 建立 FastAPI app factory 與 lifecycle 管理（asyncpg connection pool）
- 建立環境變數配置模組（.env 讀取）
- 建立三大 Service 的 router / service 骨架
- 整合 BYOA Core 作為 Agent 框架基礎

## Capabilities

### New Capabilities
- `db-schema`: PostgreSQL schema 定義與 migration，asyncpg connection pool 管理
- `app-skeleton`: FastAPI app factory、router 掛載、lifecycle events、環境配置
- `byoa-integration`: BYOA Core Agent factory 建立，為後續 Service 提供 Claude Agent 實例

### Modified Capabilities

（無既有 capability）

## Impact

- 新增 `src/persochattai/` 下的核心模組（app.py, config.py, db.py）
- 新增 SQL migration 檔案
- 新增 `.env.example`
- 所有後續 change（content-scraper, content-card, conversation, assessment, frontend）依賴此 change
