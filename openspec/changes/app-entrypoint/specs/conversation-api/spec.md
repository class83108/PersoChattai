## ADDED Requirements

### Requirement: 取消對話 API
系統 SHALL 提供 `POST /api/conversation/{conversation_id}/cancel` endpoint 取消對話。

#### Scenario: 取消進行中的對話
- **WHEN** 對話狀態為 preparing、connecting 或 active 且發送 cancel 請求
- **THEN** 系統 SHALL 呼叫 `ConversationManager.cancel_conversation()`
- **AND** 回應 SHALL 包含更新後的 `conversation_id` 和 `status`

#### Scenario: 取消已結束的對話
- **WHEN** 對話狀態為 completed、failed 或 cancelled 且發送 cancel 請求
- **THEN** 回應狀態碼 SHALL 為 409（Conflict）
- **AND** 回應 SHALL 包含錯誤訊息

#### Scenario: 取消不存在的對話
- **WHEN** conversation_id 不存在且發送 cancel 請求
- **THEN** 回應狀態碼 SHALL 為 404
