## ADDED Requirements

### Requirement: 對話狀態機
系統 SHALL 管理對話的完整生命週期，狀態轉換如下：
- `preparing` → `connecting` → `active` → `assessing` → `completed`
- `connecting` → `failed`
- `active` → `cancelled`（使用者主動取消）
- `active` → `failed`（斷線）

每次狀態變更 SHALL 同步寫入 DB `conversations.status`。

#### Scenario: 正常對話流程
- **WHEN** 使用者建立對話並完成語音互動後結束
- **THEN** 對話狀態 SHALL 依序經過 preparing → connecting → active → assessing → completed

#### Scenario: 連線失敗
- **WHEN** Gemini session 或 WebRTC 連線建立失敗
- **THEN** 對話狀態 SHALL 轉為 failed

#### Scenario: 使用者取消對話
- **WHEN** 使用者在 active 狀態主動結束對話
- **THEN** 系統 SHALL 儲存已收集的 transcript
- **AND** 對話狀態 SHALL 轉為 assessing（若有 transcript）或 cancelled（若無 transcript）

### Requirement: ConversationManager
系統 SHALL 實作 `ConversationManager` 管理所有進行中的對話。

- 持有 in-memory dict 追蹤 `conversation_id → ConversationState`
- 提供 `start_conversation()`、`end_conversation()`、`get_state()` 方法
- 對話結束時寫入完整 transcript 至 DB

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

### Requirement: 時間上限
系統 SHALL 在對話達到 15 分鐘時自動結束。

#### Scenario: 接近時間上限
- **WHEN** 對話持續 13 分鐘
- **THEN** 系統 SHALL 透過 data channel 發送警告訊息

#### Scenario: 達到時間上限
- **WHEN** 對話持續 15 分鐘
- **THEN** 系統 SHALL 自動結束對話並儲存 transcript

### Requirement: 靜默超時
系統 SHALL 在偵測到 2 分鐘無使用者音訊輸入時自動結束對話。

#### Scenario: 靜默超時觸發
- **WHEN** 使用者超過 2 分鐘未傳送音訊
- **THEN** 系統 SHALL 自動結束對話並儲存 transcript
- **AND** 透過 data channel 通知使用者

#### Scenario: 正常互動重置靜默計時
- **WHEN** 使用者在靜默計時期間傳送音訊
- **THEN** 靜默計時器 SHALL 重置為 2 分鐘

### Requirement: Scenario 生成
系統 SHALL 在建立對話時使用 BYOA `scenario_designer` skill 生成 Gemini system instruction。

#### Scenario: 根據卡片素材生成情境
- **WHEN** 使用者以 `source_type=card` 建立對話
- **THEN** 系統 SHALL 以卡片內容 + 使用者歷史呼叫 scenario_designer
- **AND** 產出的 system instruction SHALL 用於 Gemini Live session 配置

#### Scenario: 根據自由主題生成情境
- **WHEN** 使用者以 `source_type=free_topic` 建立對話
- **THEN** 系統 SHALL 以使用者提供的 topic prompt 呼叫 scenario_designer
