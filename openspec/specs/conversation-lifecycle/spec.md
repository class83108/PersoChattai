## MODIFIED Requirements

### Requirement: ConversationManager
系統 SHALL 實作 `ConversationManager` 管理所有進行中的對話。

- 持有 in-memory dict 追蹤 `conversation_id → ConversationState`
- 提供 `start_conversation()`、`end_conversation()`、`get_state()` 方法
- 對話結束時寫入完整 transcript 至 DB
- 對話結束且有 transcript 時 SHALL 觸發 `AssessmentService.evaluate()`

#### Scenario: 建立對話
- **WHEN** 呼叫 `start_conversation(user_id, source_type, source_ref)`
- **THEN** 系統 SHALL 在 DB 建立 conversation 記錄（status=preparing）
- **AND** 呼叫 scenario_designer 生成 system instruction
- **AND** 建立 Gemini Live session
- **AND** 狀態轉為 connecting

#### Scenario: 對話結束儲存 transcript
- **WHEN** 對話結束（任何原因）
- **THEN** 系統 SHALL 將收集的 transcript 寫入 DB `conversations.transcript`
- **AND** 更新 `conversations.ended_at`

#### Scenario: 對話結束觸發評估
- **WHEN** 對話結束且 transcript 不為空
- **THEN** 系統 SHALL 將狀態設為 assessing
- **AND** 呼叫 `AssessmentService.evaluate(conversation_id, user_id, transcript)`
- **AND** 評估完成後狀態轉為 completed

#### Scenario: 對話結束但無 transcript
- **WHEN** 對話結束但 transcript 為空
- **THEN** 系統 SHALL 不觸發評估
- **AND** 狀態直接轉為 cancelled
