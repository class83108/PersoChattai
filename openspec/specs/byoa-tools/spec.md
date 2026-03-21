## ADDED Requirements

### Requirement: query_cards tool 查詢素材卡片
系統 SHALL 註冊 `query_cards` BYOA tool，允許 Agent 依條件查詢素材卡片。Tool 參數包含 `source_type`（選填）、`difficulty_level`（選填）、`tags`（選填）、`keyword`（選填）、`limit`（預設 10）。Handler 委派至 `CardRepositoryProtocol.list_cards()`。

#### Scenario: 依難度查詢卡片
- **WHEN** Agent 呼叫 `query_cards` 並帶入 `difficulty_level: "B1"`
- **THEN** 回傳所有 CEFR B1 等級的卡片列表

#### Scenario: 無符合條件的卡片
- **WHEN** Agent 呼叫 `query_cards` 但無任何卡片符合篩選條件
- **THEN** 回傳空列表 `[]`

#### Scenario: 複合條件查詢
- **WHEN** Agent 呼叫 `query_cards` 並帶入 `source_type: "podcast_bbc"` 和 `tags: ["business"]`
- **THEN** 回傳同時符合來源類型和 tag 的卡片

### Requirement: create_card tool 建立學習卡片
系統 SHALL 註冊 `create_card` BYOA tool，允許 Agent 建立學習卡片。Tool 參數包含 `title`（必填）、`summary`（必填）、`keywords`（必填）、`source_type`（必填）、`source_url`（選填）、`dialogue_snippets`（選填）、`difficulty_level`（必填）、`tags`（選填）。Handler 委派至 `CardRepositoryProtocol.create()`。

#### Scenario: 成功建立卡片
- **WHEN** Agent 呼叫 `create_card` 並帶入完整參數
- **THEN** 卡片寫入資料庫並回傳含 `id` 的卡片資料

#### Scenario: 缺少必填欄位
- **WHEN** Agent 呼叫 `create_card` 但缺少 `title`
- **THEN** 回傳錯誤訊息說明缺少必填欄位

### Requirement: get_user_history tool 查詢使用者歷史
系統 SHALL 註冊 `get_user_history` BYOA tool，允許 Agent 查詢使用者的能力歷史。Tool 參數包含 `user_id`（必填）。Handler 委派至 `AssessmentService.get_user_history()`，回傳最新 snapshot + 最近 5 次評估 + 詞彙統計。

#### Scenario: 有歷史資料的使用者
- **WHEN** Agent 呼叫 `get_user_history` 並帶入已有評估紀錄的 `user_id`
- **THEN** 回傳包含 `latest_snapshot`、`recent_assessments`、`vocabulary_stats` 的 dict

#### Scenario: 新使用者無歷史
- **WHEN** Agent 呼叫 `get_user_history` 並帶入無任何紀錄的 `user_id`
- **THEN** 回傳 `latest_snapshot: null`、`recent_assessments: []`、`vocabulary_stats` 含零值

### Requirement: Tool registry 按 Agent 角色組裝
系統 SHALL 為每個 Agent 建立專屬的 ToolRegistry，只包含該 Agent 需要的 tools。Content agent 包含 `create_card`；Conversation agent 包含 `query_cards` + `get_user_history`；Assessment agent 包含 `get_user_history`。

#### Scenario: Content agent 只能存取 create_card
- **WHEN** content agent 嘗試呼叫 tool
- **THEN** 只有 `create_card` 出現在可用 tool 列表中

#### Scenario: Conversation agent 能存取 query_cards 和 get_user_history
- **WHEN** conversation agent 的 tool registry 被查詢
- **THEN** 包含 `query_cards` 和 `get_user_history` 兩個 tools
