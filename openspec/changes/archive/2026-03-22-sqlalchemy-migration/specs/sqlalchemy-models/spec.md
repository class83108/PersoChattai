## ADDED Requirements

### Requirement: SQLAlchemy DeclarativeBase
系統 SHALL 定義 `Base` class（繼承 `DeclarativeBase`）作為所有 ORM model 的基底，放置於 `database/base.py`。

#### Scenario: Base 可被所有 table model 繼承
- **WHEN** import `persochattai.database.base.Base`
- **THEN** 它 SHALL 為 `sqlalchemy.orm.DeclarativeBase` 的子類

### Requirement: ORM model 對應全部 8 張表
系統 SHALL 在 `database/tables.py` 定義 ORM model，與現有 DB schema 完全一致。
涵蓋：UserTable, CardTable, ConversationTable, AssessmentTable, UserVocabularyTable, UserLevelSnapshotTable, ApiUsageTable, ModelConfigTable。

#### Scenario: UserTable 欄位對應
- **WHEN** 檢視 `UserTable` model
- **THEN** 它 SHALL 包含 `id` (UUID PK), `display_name` (Text), `current_level` (Text nullable), `created_at` (TIMESTAMPTZ)

#### Scenario: CardTable 欄位對應
- **WHEN** 檢視 `CardTable` model
- **THEN** 它 SHALL 包含 `id` (UUID PK), `source_type`, `source_url` (nullable), `title`, `summary`, `keywords` (JSONB), `dialogue_snippets` (JSONB), `difficulty_level` (nullable), `tags` (ARRAY), `created_at`

#### Scenario: ConversationTable 欄位對應
- **WHEN** 檢視 `ConversationTable` model
- **THEN** 它 SHALL 包含 `id` (UUID PK), `user_id` (FK→users), `conversation_type`, `source_type`, `source_ref` (nullable), `system_instruction` (nullable), `started_at`, `ended_at` (nullable), `transcript` (JSONB), `status`

#### Scenario: AssessmentTable 欄位對應
- **WHEN** 檢視 `AssessmentTable` model
- **THEN** 它 SHALL 包含所有量化指標欄位（mtld, vocd_d, k1_ratio, k2_ratio, awl_ratio 等）和質性分析欄位（cefr_level, suggestions, raw_analysis 等）
- **AND** `conversation_id` 和 `user_id` SHALL 為外鍵

#### Scenario: JSONB 欄位正確序列化
- **WHEN** 存取 CardTable.keywords 或 ConversationTable.transcript 等 JSONB 欄位
- **THEN** 系統 SHALL 自動在 Python dict/list 與 JSONB 間轉換

### Requirement: ORM model 與 Pydantic model 並存
SQLAlchemy ORM model 僅用於 DB 操作，Pydantic model（`models.py`）繼續用於 API 層。Repository SHALL 負責兩者間的轉換。

#### Scenario: Repository 回傳 Pydantic model 或 dict
- **WHEN** repository 方法查詢 DB
- **THEN** 它 SHALL 將 ORM 物件轉換為 Pydantic model 或 dict 後回傳
- **AND** caller SHALL 不直接操作 ORM 物件
