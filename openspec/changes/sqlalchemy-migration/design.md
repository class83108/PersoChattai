## Context

目前資料層使用 asyncpg raw SQL + global pool singleton + repository pattern。7 個 repository 各自用 `pool.acquire()` 取 connection 執行 raw SQL。Pydantic models (`models.py`) 用於 API 層資料傳遞，與 DB 無直接關聯。Migration 以 3 個手動 SQL 檔管理，無版本追蹤。

## Goals / Non-Goals

**Goals:**
- 將 DB 存取從 asyncpg raw SQL 遷移至 SQLAlchemy ORM + AsyncSession
- 用 Alembic 管理 schema migration，含版本追蹤
- 保持所有現有 API 行為與測試覆蓋不變
- Repository 接受 AsyncSession 注入，提升可測試性

**Non-Goals:**
- 不改動 Pydantic models（API 層繼續用 Pydantic）
- 不改動 API endpoint 行為
- 不引入 Unit of Work pattern 或 repository 抽象 Protocol（保持簡單）
- 不做 DB schema 變更（只遷移工具鏈）

## Decisions

### D-1: SQLAlchemy ORM model 與 Pydantic model 並存

**選擇**: SQLAlchemy ORM models 放 `src/persochattai/database/tables.py`，Pydantic models 保持不變。Repository 內部用 ORM，對外回傳 Pydantic model 或 dict。

**理由**: 避免大規模改動上層 service/router。ORM model 負責 DB 映射，Pydantic model 負責 API schema — 職責分離。

**替代方案**: 用 SQLModel 合併兩者 → 依賴較新、社群較小、與 BYOA Core 的 Pydantic 整合可能有衝突。

### D-2: 新增 `database/` package 集中 DB 相關模組

**選擇**: 建立 `src/persochattai/database/` package，包含：
- `engine.py` — async engine + session factory
- `tables.py` — 全部 SQLAlchemy ORM models
- `base.py` — DeclarativeBase

**理由**: 集中管理，避免 circular import。`db.py` 將被此 package 取代。

### D-3: Repository 注入 AsyncSession（非 engine/pool）

**選擇**: Repository constructor 接收 `AsyncSession`，由 caller（router/service）負責 session lifecycle。

**理由**:
- 與 FastAPI `Depends()` 整合自然
- 測試時可直接注入 mock session
- Session-per-request pattern 是 FastAPI + SQLAlchemy 的最佳實踐

### D-4: Alembic async mode + app 啟動自動 migrate

**選擇**: Alembic 設定使用 `async` 模式。App lifespan 啟動時自動執行 `alembic upgrade head`。

**理由**: VPS 單機部署，不需複雜的 migration 策略。開發環境也受益於自動 migrate。

**替代方案**: 手動跑 `alembic upgrade` → 容易忘記，部署流程多一步。

### D-5: 保留 asyncpg 作為 SQLAlchemy driver

**選擇**: URL scheme 使用 `postgresql+asyncpg://`，asyncpg 從直接依賴變為 SQLAlchemy 的 driver。

**理由**: asyncpg 效能最佳，且已在用。psycopg3 async 也可以但無遷移理由。

## Risks / Trade-offs

- **[效能微降]** ORM overhead vs raw SQL → 對此專案規模可忽略（~10 用戶）。若未來需要可針對 hot path 用 `text()` 或 Core query。
- **[測試改動量大]** 7 個 repository + 所有 step definitions 需更新 → 逐 repository 改寫，每改完一個跑測試確認。
- **[Alembic initial migration]** 需產出與現有 schema 完全一致的 migration → 用 `--autogenerate` 比對現有 DB 產出，再 review。
- **[JSONB 欄位處理]** SQLAlchemy 的 JSONB type 與 asyncpg 的 JSON codec 行為可能不同 → 測試覆蓋 JSONB 讀寫。
