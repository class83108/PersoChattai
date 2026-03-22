### Requirement: 建立對話 API
系統 SHALL 提供 `POST /api/conversation/start` endpoint 建立新對話。

Request body:
```json
{
  "user_id": "uuid",
  "source_type": "card | pdf | free_topic",
  "source_ref": "card_id | pdf filename | topic prompt"
}
```

#### Scenario: 成功建立對話
- **WHEN** 發送有效的 POST 請求至 `/api/conversation/start`
- **THEN** 回應狀態碼 SHALL 為 201
- **AND** 回應 SHALL 包含 `conversation_id` 和 `status: "preparing"`

#### Scenario: 缺少必要欄位
- **WHEN** 發送缺少 `user_id` 或 `source_type` 的 POST 請求
- **THEN** 回應狀態碼 SHALL 為 422

### Requirement: 查詢對話狀態 API
系統 SHALL 提供 `GET /api/conversation/{conversation_id}` endpoint 查詢對話狀態。

#### Scenario: 查詢存在的對話
- **WHEN** 發送 GET 請求且 conversation_id 存在
- **THEN** 回應 SHALL 包含 `conversation_id`、`status`、`started_at`

#### Scenario: 查詢不存在的對話
- **WHEN** 發送 GET 請求且 conversation_id 不存在
- **THEN** 回應狀態碼 SHALL 為 404

### Requirement: 結束對話 API
系統 SHALL 提供 `POST /api/conversation/{conversation_id}/end` endpoint 結束對話。

#### Scenario: 結束進行中的對話
- **WHEN** 對話狀態為 active 且發送 end 請求
- **THEN** 系統 SHALL 儲存 transcript 並開始評估流程
- **AND** 回應 SHALL 包含 `status: "assessing"`

#### Scenario: 結束非 active 對話
- **WHEN** 對話狀態不是 active 且發送 end 請求
- **THEN** 回應狀態碼 SHALL 為 409（Conflict）

### Requirement: 列出對話歷史 API
系統 SHALL 提供 `GET /api/conversation/history/{user_id}` endpoint 列出使用者的對話歷史。

#### Scenario: 列出對話歷史
- **WHEN** 發送 GET 請求
- **THEN** 回應 SHALL 包含該使用者所有對話的摘要列表（id, status, started_at, ended_at, source_type）
- **AND** 結果 SHALL 按 started_at 降序排列

#### Scenario: 無對話歷史
- **WHEN** 使用者沒有任何對話記錄
- **THEN** 回應 SHALL 為空陣列 `[]`

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
