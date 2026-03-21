## Context

PersoChattai 是全新專案，目前只有 pyproject.toml、空目錄結構、CI pipeline。需要建立所有基礎設施讓後續功能開發能夠開始。

專案部署在單台 VPS，使用者為小圈子（~10 人），API key 由 server 端統一管理。

## Goals / Non-Goals

**Goals:**
- PostgreSQL schema 可透過 SQL 檔案一鍵建立
- FastAPI app 能啟動、回應 health check
- asyncpg connection pool 正確管理生命週期
- 環境變數配置集中管理，缺少必要變數時明確報錯
- 三大 Service 的 router 骨架掛載完成
- BYOA Core Agent 可被各 Service 實例化

**Non-Goals:**
- 不實作任何業務邏輯（爬蟲、對話、評估等）
- 不做 DB migration 工具整合（初期手動跑 SQL）
- 不做使用者認證（小圈子使用，後續 P1 再加）
- 不做前端頁面（Spec 007-frontend 負責）

## Decisions

### D-1: asyncpg 直連，不用 ORM

**決定**：使用 asyncpg + 手寫 SQL

**替代方案**：SQLAlchemy async + Alembic

**理由**：
- Schema 明確（6 張表），不需要 ORM 的抽象層
- asyncpg 效能最好，直接寫 SQL 更透明
- 避免 SQLAlchemy async session 管理的複雜度
- 初期用 SQL 檔案做 migration，之後需要時再加 Alembic

### D-2: Pydantic model 定義所有資料結構

**決定**：DB 資料進出都經過 Pydantic model 轉換

**理由**：
- 統一格式控制，符合專案 CLAUDE.md 規範
- FastAPI 自動生成 OpenAPI schema
- 型別安全，pyright 可檢查

**結構**：
```
src/persochattai/models.py  — 共用的 Pydantic models（對應 DB schema）
```

### D-3: FastAPI app factory pattern

**決定**：`create_app()` factory function，不用全域 app 變數

**理由**：
- 測試時可建立獨立的 app 實例
- lifecycle events（DB pool 建立/關閉）集中管理
- 方便未來加 middleware

### D-4: BYOA Agent factory per Service

**決定**：每個 Service 有自己的 Agent factory，產出針對該 Service 優化的 Agent 實例

**理由**：
- scenario_designer / transcript_evaluator / content_summarizer 各自需要不同的 system prompt、tools、skills
- 分開管理避免 Agent 配置互相干擾
- 共用同一個 ClaudeProvider 實例（共用 API key 和 UsageMonitor）

### D-5: 環境變數分層

**決定**：
```python
@dataclass
class Settings:
    db_url: str
    anthropic_api_key: str
    gemini_api_key: str
    debug: bool = False
```

**讀取順序**：`.env` 檔 → 環境變數 → 預設值。缺少必要變數時 raise 明確錯誤。

## Risks / Trade-offs

**[手寫 SQL 沒有 migration 版本控制]** → 初期可接受，schema 變更時手動管理 SQL 檔案。累積超過 5 次 schema 變更後考慮加 Alembic。

**[沒有使用者認證]** → 小圈子使用期間透過 VPS 防火牆 + 簡單的 API key header 限制存取，非長期方案。

**[asyncpg connection pool 大小]** → 預設 min=2, max=10，單台 VPS + 少量使用者足夠。
