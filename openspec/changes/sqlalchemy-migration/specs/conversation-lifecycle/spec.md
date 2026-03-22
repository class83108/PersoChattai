## MODIFIED Requirements

### Requirement: ConversationManager
系統 SHALL 實作 `ConversationManager` 管理所有進行中的對話。

- 持有 in-memory dict 追蹤 `conversation_id → ConversationState`
- 提供 `start_conversation()`、`end_conversation()`、`cancel_conversation()`、`get_state()` 方法
- 對話結束時寫入完整 transcript 至 DB
- 對話結束且有 transcript 時 SHALL 觸發 `AssessmentService.evaluate()`
- 對話進入 ACTIVE 狀態後 SHALL 自動排程 timeout task 和 silence monitor
- ConversationManager SHALL 持有 session factory，在需要 DB 操作時自行建立 session

#### Scenario: 建立對話
- **WHEN** 呼叫 `start_conversation(user_id, source_type, source_ref)`
- **THEN** 系統 SHALL 建立 AsyncSession 並透過 repository 在 DB 建立 conversation 記錄（status=preparing）
- **AND** 呼叫 scenario_designer 生成 system instruction
- **AND** 建立 Gemini Live session
- **AND** 狀態轉為 connecting

#### Scenario: 對話結束儲存 transcript
- **WHEN** 對話結束（任何原因）
- **THEN** 系統 SHALL 透過 AsyncSession 將 transcript 寫入 DB
- **AND** 更新 `conversations.ended_at`
