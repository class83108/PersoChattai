## ADDED Requirements

### Requirement: 建立使用者 API
系統 SHALL 提供 `POST /api/users` endpoint，接受 `display_name` 建立使用者或回傳既有使用者。

Request body:
```json
{
  "display_name": "string (1-20 chars)"
}
```

#### Scenario: 建立新使用者
- **WHEN** 發送 POST 請求，`display_name` 不存在於 DB
- **THEN** 系統 SHALL 建立新 user row（生成 UUID）
- **AND** 回應狀態碼 SHALL 為 201
- **AND** 回應 SHALL 包含 `id`（UUID）和 `display_name`

#### Scenario: 暱稱已存在
- **WHEN** 發送 POST 請求，`display_name` 已存在於 DB
- **THEN** 系統 SHALL 回傳該既有使用者的 `id` 和 `display_name`
- **AND** 回應狀態碼 SHALL 為 200

#### Scenario: 暱稱格式無效
- **WHEN** 發送 POST 請求，`display_name` 為空字串或超過 20 字
- **THEN** 回應狀態碼 SHALL 為 422
- **AND** 回應 SHALL 包含驗證錯誤訊息

### Requirement: 查詢使用者 API
系統 SHALL 提供 `GET /api/users/{user_id}` endpoint 驗證使用者是否存在。

#### Scenario: 使用者存在
- **WHEN** 發送 GET 請求，`user_id` 對應的 user 存在
- **THEN** 回應狀態碼 SHALL 為 200
- **AND** 回應 SHALL 包含 `id`、`display_name`、`current_level`

#### Scenario: 使用者不存在
- **WHEN** 發送 GET 請求，`user_id` 不存在於 DB
- **THEN** 回應狀態碼 SHALL 為 404

### Requirement: 暱稱唯一約束
系統 SHALL 在 `users.display_name` 欄位設置 UNIQUE 約束。

#### Scenario: DB 層級唯一性保障
- **WHEN** 兩個並發請求嘗試建立相同 `display_name` 的使用者
- **THEN** 僅一個 SHALL 成功建立，另一個 SHALL 回傳既有使用者

### Requirement: 前端暱稱 modal
系統 SHALL 在使用者首次進站時顯示暱稱輸入 modal，阻斷操作直到完成。

#### Scenario: 首次進站
- **WHEN** 頁面載入且 localStorage 無 `persochattai_user_id`
- **THEN** 系統 SHALL 顯示全頁 modal 要求輸入暱稱
- **AND** modal 外的內容 SHALL 不可互動

#### Scenario: 提交暱稱成功
- **WHEN** 使用者輸入暱稱並提交
- **THEN** 系統 SHALL 呼叫 `POST /api/users`
- **AND** 將回傳的 `id` 和 `display_name` 存入 localStorage
- **AND** 關閉 modal

#### Scenario: 回訪使用者
- **WHEN** 頁面載入且 localStorage 有 `persochattai_user_id`
- **THEN** 系統 SHALL 呼叫 `GET /api/users/{user_id}` 驗證
- **AND** 若 200，navbar SHALL 顯示暱稱
- **AND** 若 404，SHALL 清除 localStorage 並顯示 modal

### Requirement: Navbar 使用者顯示
系統 SHALL 在 navbar 顯示當前使用者暱稱及換人功能。

#### Scenario: 顯示暱稱
- **WHEN** 使用者已識別
- **THEN** navbar SHALL 顯示 `display_name`

#### Scenario: 換人
- **WHEN** 使用者點擊「換人」按鈕
- **THEN** 系統 SHALL 清除 localStorage 中的 `persochattai_user_id` 和 `persochattai_display_name`
- **AND** 顯示暱稱輸入 modal
