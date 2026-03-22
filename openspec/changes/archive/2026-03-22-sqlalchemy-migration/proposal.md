## Why

目前資料層使用 asyncpg raw SQL + 手動管理 migration 檔案，隨功能增長維護成本上升且缺乏 schema 版本追蹤。遷移至 SQLAlchemy ORM + Alembic 可獲得型別安全的查詢、自動化 migration 管理、以及更好的可維護性。

## What Changes

- **BREAKING**: 移除 asyncpg 直接依賴，改用 SQLAlchemy async engine + AsyncSession
- 新增 SQLAlchemy ORM models 對應現有 8 張表（users, cards, conversations, assessments, user_vocabulary, user_level_snapshots, api_usage, model_config）
- 新增 Alembic 設定與 initial migration（等價於現有 `migrations/001~003`）
- 改寫全部 7 個 repository（CardRepository, ConversationRepository, AssessmentRepository, UsageRepository, UserVocabularyRepository, LevelSnapshotRepository, ModelConfigRepository）使用 AsyncSession
- `db.py` 從 asyncpg pool 改為 SQLAlchemy async_sessionmaker
- `app.py` lifespan 整合 SQLAlchemy engine lifecycle
- 移除 `migrations/` 目錄，由 Alembic 接管

## Capabilities

### New Capabilities
- `sqlalchemy-models`: SQLAlchemy ORM model 定義，對應全部 8 張 DB 表
- `alembic-migration`: Alembic 設定、initial migration、與 app lifespan 整合
- `async-session-management`: SQLAlchemy async engine + session 生命週期管理

### Modified Capabilities
- `app-bootstrap`: lifespan 從 asyncpg pool init 改為 SQLAlchemy engine init + Alembic migration
- `conversation-api`: repository 層改用 AsyncSession（API 行為不變）
- `conversation-lifecycle`: repository 層改用 AsyncSession（狀態機行為不變）

## Impact

- **依賴變更**: 新增 `sqlalchemy[asyncio]`, `alembic`, `asyncpg`（作為 SQLAlchemy driver）；移除 asyncpg 作為直接依賴
- **所有 repository**: 查詢語法從 raw SQL 改為 SQLAlchemy ORM
- **db.py**: 連線管理完全重寫
- **app.py**: lifespan 初始化流程調整
- **所有測試**: repository 相關的 mock/fixture 需更新為 AsyncSession
- **config.py**: DB_URL 格式可能需加 `+asyncpg` scheme
