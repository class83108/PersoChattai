## ADDED Requirements

### Requirement: Alembic 設定
系統 SHALL 在專案根目錄設定 Alembic，使用 async mode 搭配 asyncpg driver。

#### Scenario: Alembic 目錄結構
- **WHEN** 檢視專案根目錄
- **THEN** SHALL 存在 `alembic.ini` 和 `alembic/` 目錄
- **AND** `alembic/env.py` SHALL 使用 async engine 執行 migration

#### Scenario: Alembic 認識所有 ORM model
- **WHEN** Alembic autogenerate 偵測 schema 差異
- **THEN** 它 SHALL 透過 `Base.metadata` 取得全部 8 張表的定義

### Requirement: Initial migration
系統 SHALL 包含一個 initial migration，等價於現有 `migrations/001_init.sql` + `002_api_usage.sql` + `003_model_config.sql` 的合併。

#### Scenario: Initial migration 涵蓋全部表
- **WHEN** 在空 DB 執行 `alembic upgrade head`
- **THEN** 系統 SHALL 建立全部 8 張表，含索引與外鍵約束
- **AND** 結果 SHALL 與現有手動 migration 產出的 schema 一致

### Requirement: App 啟動自動 migrate
系統 SHALL 在 app lifespan startup 階段自動執行 Alembic migration 至最新版本。

#### Scenario: 啟動時自動 migrate
- **WHEN** app 啟動
- **THEN** 系統 SHALL 執行等價於 `alembic upgrade head` 的操作
- **AND** 若 DB 已在最新版本，SHALL 為 no-op

#### Scenario: Migration 失敗時 app 不啟動
- **WHEN** migration 執行失敗
- **THEN** app SHALL 拋出例外，不繼續啟動流程
