## 1. 基礎建設：SQLAlchemy + Alembic 設定

- [x] 1.1 新增 `sqlalchemy[asyncio]` 和 `alembic` 至 pyproject.toml 依賴
- [x] 1.2 建立 `database/` package：`base.py`（DeclarativeBase）、`tables.py`（8 張表 ORM models）、`engine.py`（async engine + session factory）
- [x] 1.3 設定 Alembic：`alembic.ini` + `alembic/env.py`（async mode）
- [x] 1.4 產出 initial migration（等價於現有 001~003 SQL 合併）
- [x] 1.5 建立 `database/engine.py` 的 `run_migrations()` 函式供 lifespan 呼叫

## 2. Repository 改寫

- [x] 2.1 改寫 `content/repository.py`（CardRepository）：asyncpg → AsyncSession
- [x] 2.2 改寫 `conversation/repository.py`（ConversationRepository）：asyncpg → AsyncSession
- [x] 2.3 改寫 `assessment/repository.py`（AssessmentRepository）：asyncpg → AsyncSession
- [x] 2.4 改寫 `assessment/vocabulary_repository.py`（UserVocabularyRepository）：asyncpg → AsyncSession
- [x] 2.5 改寫 `assessment/snapshot_repository.py`（LevelSnapshotRepository）：asyncpg → AsyncSession
- [x] 2.6 改寫 `usage/repository.py`（UsageRepository）：asyncpg → AsyncSession
- [x] 2.7 改寫 `usage/model_config_repository.py`（ModelConfigRepository）：asyncpg → AsyncSession

## 3. App 整合

- [x] 3.1 改寫 `db.py` → 移除 asyncpg pool，改為 SQLAlchemy engine 管理
- [x] 3.2 更新 `app.py` lifespan：engine init → auto migrate → session factory → service 初始化 → dispose
- [x] 3.3 更新 `config.py`：DB_URL 格式支援 `postgresql+asyncpg://`（engine.py 自動轉換）
- [x] 3.4 新增 FastAPI dependency `get_session` 提供 session-per-request（在 engine.py）

## 4. 測試更新

- [x] 4.1 更新 test fixtures：asyncpg pool mock → AsyncSession mock
- [x] 4.2 更新 content service 相關 step definitions（無需修改）
- [x] 4.3 更新 conversation service 相關 step definitions（無需修改）
- [x] 4.4 更新 assessment service 相關 step definitions（無需修改）
- [x] 4.5 更新 usage service 相關 step definitions
- [x] 4.6 更新 app bootstrap 相關 step definitions
- [ ] 4.7 新增 database/ package 測試（engine init、session lifecycle）— 延後

## 5. 清理

- [x] 5.1 移除 `migrations/` 目錄（由 Alembic 接管）
- [x] 5.2 移除 `db.py` 中的 asyncpg pool 相關 code（已整合至 database/ package）
- [x] 5.3 執行 `ruff check . --fix && ruff format . && pyright` 確認品質
- [x] 5.4 執行完整測試套件確認全部通過
