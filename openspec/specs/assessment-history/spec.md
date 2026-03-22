## ADDED Requirements

### Requirement: Assessment history list
報告頁面 SHALL 顯示使用者的評估歷史列表。

#### Scenario: History loads via HTMX
- **WHEN** 報告頁面載入
- **THEN** 透過 HTMX 載入評估歷史列表

#### Scenario: History item shows key info
- **WHEN** 歷史列表載入完成
- **THEN** 每筆顯示日期、CEFR 等級、三維度分數摘要

#### Scenario: Empty history
- **WHEN** 沒有評估記錄
- **THEN** 顯示空狀態提示

### Requirement: Assessment detail expandable
每筆評估記錄 SHALL 可展開查看詳細內容。

#### Scenario: Expand assessment shows detail
- **WHEN** 使用者點擊展開一筆評估
- **THEN** 顯示完整的三維度分析、質性評估文字、NLP 量化指標

### Requirement: AssessmentRepository
系統 SHALL 實作 `AssessmentRepository`（Protocol-based），提供評估結果的 CRUD 操作。

#### Scenario: 建立評估記錄
- **WHEN** 呼叫 `create(assessment_data)`
- **THEN** 系統 SHALL 在 assessments 表建立記錄並回傳含 id 的完整資料

#### Scenario: 查詢單一評估
- **WHEN** 呼叫 `get_by_id(assessment_id)`
- **THEN** 系統 SHALL 回傳該評估的完整資料（含量化指標和質性分析）

#### Scenario: 查詢使用者評估歷史
- **WHEN** 呼叫 `list_by_user(user_id, limit, offset)`
- **THEN** 系統 SHALL 回傳該使用者的評估列表，依建立時間降序排列

### Requirement: UserVocabularyRepository
系統 SHALL 實作 `UserVocabularyRepository`，管理使用者詞彙庫。

#### Scenario: 新增或更新詞彙
- **WHEN** 呼叫 `upsert_words(user_id, words, conversation_id)`
- **THEN** 新詞 SHALL 被新增（occurrence_count=1）
- **AND** 已知詞 SHALL 累加 occurrence_count

#### Scenario: 查詢詞彙統計
- **WHEN** 呼叫 `get_vocabulary_stats(user_id)`
- **THEN** 系統 SHALL 回傳：
  - `total_words`: int（詞彙庫總字數）
  - `recent_words`: list（最近 N 個新增詞彙）

### Requirement: LevelSnapshotRepository
系統 SHALL 實作 `LevelSnapshotRepository`，管理使用者等級快照。

#### Scenario: 建立 snapshot
- **WHEN** 呼叫 `create_snapshot(user_id, snapshot_data)`
- **THEN** 系統 SHALL 在 user_level_snapshots 表建立記錄

#### Scenario: 查詢最新 snapshot
- **WHEN** 呼叫 `get_latest(user_id)`
- **THEN** 系統 SHALL 回傳該使用者最新的 level_snapshot

#### Scenario: 查詢 snapshot 歷史
- **WHEN** 呼叫 `list_snapshots(user_id, limit)`
- **THEN** 系統 SHALL 回傳 snapshot 列表，依日期降序排列

### Requirement: Assessment REST API
系統 SHALL 提供 REST API 查詢評估結果和使用者歷史。

#### Scenario: 查詢單一評估
- **WHEN** GET /api/assessment/{assessment_id}
- **THEN** 回傳該評估的完整資料（含量化指標和質性分析）
- **AND** 狀態碼 SHALL 為 200

#### Scenario: 評估不存在
- **WHEN** GET /api/assessment/{不存在的 id}
- **THEN** 狀態碼 SHALL 為 404

#### Scenario: 查詢使用者評估歷史
- **WHEN** GET /api/assessment/user/{user_id}/history?limit=10&offset=0
- **THEN** 回傳該使用者的評估列表
- **AND** 支援分頁

#### Scenario: 查詢使用者詞彙統計
- **WHEN** GET /api/assessment/user/{user_id}/vocabulary
- **THEN** 回傳詞彙庫統計（total_words、recent_words）

#### Scenario: 查詢使用者成長追蹤
- **WHEN** GET /api/assessment/user/{user_id}/progress
- **THEN** 回傳最新 level_snapshot + 最近 5 次評估摘要

### Requirement: get_user_history BYOA Tool
系統 SHALL 提供 `get_user_history` tool 供 BYOA Agent 查詢使用者能力摘要。

#### Scenario: Agent 查詢使用者歷史
- **WHEN** Agent 呼叫 `get_user_history(user_id)`
- **THEN** 系統 SHALL 回傳：
  - 最新 level_snapshot
  - 最近 5 次 assessments 摘要
  - user_vocabulary 統計（詞彙庫大小 + 最近新增詞）

#### Scenario: 新使用者無歷史
- **WHEN** 使用者沒有任何評估記錄
- **THEN** 系統 SHALL 回傳空的歷史（snapshot 為 null、assessments 為空列表）
