## ADDED Requirements

### Requirement: Database connection pool 管理
系統 SHALL 在 FastAPI app 啟動時建立 asyncpg connection pool，關閉時釋放。

#### Scenario: App 啟動時建立連線池
- **WHEN** FastAPI app 啟動 lifespan 事件觸發
- **THEN** asyncpg connection pool 建立成功，min_size=2, max_size=10

#### Scenario: App 關閉時釋放連線池
- **WHEN** FastAPI app 關閉 lifespan 事件觸發
- **THEN** asyncpg connection pool 正確關閉，無連線洩漏

#### Scenario: DB 連線失敗時明確報錯
- **WHEN** DB_URL 無效或 PostgreSQL 無法連線
- **THEN** 系統 SHALL 拋出明確錯誤訊息並阻止 app 啟動

### Requirement: Schema migration 執行
系統 SHALL 提供 SQL 檔案可一鍵建立所有資料表。

#### Scenario: 首次建立所有資料表
- **WHEN** 對空資料庫執行 migration SQL
- **THEN** 建立 users, cards, conversations, assessments, user_vocabulary, user_level_snapshots 六張表

#### Scenario: 重複執行 migration 不報錯
- **WHEN** 對已存在表的資料庫重複執行 migration SQL
- **THEN** 使用 IF NOT EXISTS，不產生錯誤

### Requirement: 資料表 schema 正確性
所有資料表 SHALL 符合 design-doc.md 定義的 schema。

#### Scenario: users 表結構正確
- **WHEN** 查詢 users 表結構
- **THEN** 包含 id(uuid PK), display_name(text), current_level(text nullable), created_at(timestamptz)

#### Scenario: cards 表結構正確
- **WHEN** 查詢 cards 表結構
- **THEN** 包含 id(uuid PK), source_type(text), source_url(text), title(text), summary(text), keywords(jsonb), dialogue_snippets(jsonb), difficulty_level(text), tags(text[]), created_at(timestamptz)

#### Scenario: conversations 表結構正確
- **WHEN** 查詢 conversations 表結構
- **THEN** 包含 id(uuid PK), user_id(uuid FK→users), conversation_type(text), source_type(text), source_ref(text), system_instruction(text), started_at(timestamptz), ended_at(timestamptz nullable), transcript(jsonb), status(text)

#### Scenario: assessments 表結構正確
- **WHEN** 查詢 assessments 表結構
- **THEN** 包含所有量化指標欄位（mtld, vocd_d, k1_ratio, k2_ratio, awl_ratio 等）與質性分析欄位（cefr_level, lexical_assessment 等）

#### Scenario: user_vocabulary 表結構正確
- **WHEN** 查詢 user_vocabulary 表結構
- **THEN** 包含 id(uuid PK), user_id(uuid FK), word(text), first_seen_at(timestamptz), first_seen_conversation_id(uuid FK), occurrence_count(int)，且 (user_id, word) 有 UNIQUE 約束

#### Scenario: user_level_snapshots 表結構正確
- **WHEN** 查詢 user_level_snapshots 表結構
- **THEN** 包含 id(uuid PK), user_id(uuid FK), snapshot_date(date), cefr_level(text), avg_mtld(float), avg_vocd_d(float), vocabulary_size(int), strengths(text[]), weaknesses(text[]), conversation_count(int), created_at(timestamptz)
