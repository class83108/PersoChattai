## MODIFIED Requirements

### Requirement: ConversationManager
系統 SHALL 實作 `ConversationManager` 管理所有進行中的對話。

- 持有 in-memory dict 追蹤 `conversation_id → ConversationState`
- 提供 `start_conversation()`、`end_conversation()`、`cancel_conversation()`、`get_state()` 方法
- 對話結束時寫入完整 transcript 至 DB
- 對話結束且有 transcript 時 SHALL 觸發 `AssessmentService.evaluate()`
- 對話進入 ACTIVE 狀態後 SHALL 自動排程 timeout task 和 silence monitor

#### Scenario: 建立對話
- **WHEN** 呼叫 `start_conversation(user_id, source_type, source_ref)`
- **THEN** 系統 SHALL 在 DB 建立 conversation 記錄（status=preparing）
- **AND** 呼叫 scenario_designer 生成 system instruction
- **AND** 建立 Gemini Live session
- **AND** 狀態轉為 connecting

#### Scenario: 對話進入 ACTIVE 後排程 timeout
- **WHEN** 對話狀態成功轉為 active
- **THEN** 系統 SHALL 建立 asyncio.Task 在 13 分鐘後發送 time_warning notification
- **AND** 在 15 分鐘後自動呼叫 `_on_time_limit_reached` 結束對話
- **AND** timeout task SHALL 存入 `_timeout_tasks[conversation_id]`

#### Scenario: 對話進入 ACTIVE 後啟動 silence monitor
- **WHEN** 對話狀態成功轉為 active
- **THEN** 系統 SHALL 初始化 `_silence_timers[conversation_id]` 為當前時間
- **AND** 建立 periodic check task（每 10 秒）
- **AND** 當 last audio timestamp 距現在 > 120 秒時 SHALL 觸發 `handle_silence_timeout`

#### Scenario: 取消對話
- **WHEN** 呼叫 `cancel_conversation(conversation_id)`
- **AND** 對話狀態為 preparing、connecting 或 active
- **THEN** 若為 active 且有 transcript，系統 SHALL 儲存 transcript 後轉為 assessing
- **AND** 若無 transcript 或非 active，系統 SHALL 直接轉為 cancelled
- **AND** 清理 timeout task 和 silence timer

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

#### Scenario: 對話結束清理 timeout
- **WHEN** 對話結束（end、cancel、timeout、silence）
- **THEN** 系統 SHALL cancel 對應的 timeout task
- **AND** 清除 silence timer
