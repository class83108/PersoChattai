## MODIFIED Requirements

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
- **AND** `user_id` 存在於 `users` 表
- **THEN** 回應狀態碼 SHALL 為 201
- **AND** 回應 SHALL 包含 `conversation_id` 和 `status: "preparing"`
- **AND** repository SHALL 透過 AsyncSession 存取 DB

#### Scenario: user_id 不存在
- **WHEN** 發送 POST 請求，`user_id` 不存在於 `users` 表
- **THEN** 回應狀態碼 SHALL 為 404
- **AND** 回應 SHALL 包含 `"使用者不存在，請先建立帳號"`

#### Scenario: 缺少必要欄位
- **WHEN** 發送缺少 `user_id` 或 `source_type` 的 POST 請求
- **THEN** 回應狀態碼 SHALL 為 422

### Requirement: 列出對話歷史 API
系統 SHALL 提供 `GET /api/conversation/history/{user_id}` endpoint 列出使用者的對話歷史。

#### Scenario: 列出對話歷史
- **WHEN** 發送 GET 請求
- **THEN** 回應 SHALL 包含該使用者所有對話的摘要列表（id, status, started_at, ended_at, source_type）
- **AND** 結果 SHALL 按 started_at 降序排列
- **AND** 查詢 SHALL 透過 SQLAlchemy ORM 執行
