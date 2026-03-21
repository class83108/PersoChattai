## ADDED Requirements

### Requirement: Settings 包含模型 fallback 欄位

`Settings` SHALL 包含 `claude_model` 和 `gemini_model` 欄位，有預設值，可透過環境變數 `CLAUDE_MODEL` / `GEMINI_MODEL` 覆蓋。這些值在 DB 無 active model 時作為 fallback。

#### Scenario: 使用預設模型
- **WHEN** 環境變數未設定 `CLAUDE_MODEL` 和 `GEMINI_MODEL`
- **THEN** `Settings.claude_model` 為 `'claude-sonnet-4-20250514'`
- **THEN** `Settings.gemini_model` 為 `'gemini-2.0-flash'`

#### Scenario: 環境變數覆蓋模型
- **WHEN** 環境變數設定 `CLAUDE_MODEL=claude-opus-4-20250514`
- **THEN** `Settings.claude_model` 為 `'claude-opus-4-20250514'`

### Requirement: 模型配置持久化於 DB

系統 SHALL 在 `model_config` table 中儲存可選模型及其定價資訊。每個 provider（claude/gemini）有一個 active model。

#### Scenario: 啟動時 seed 預設模型
- **WHEN** `model_config` table 為空
- **THEN** 自動 seed Claude 三個模型（sonnet, opus, haiku）和 Gemini 兩個模型（2.0-flash, 2.5-flash）
- **THEN** 每個 provider 有一個 `is_active = TRUE` 的模型

#### Scenario: 重啟後保留模型配置
- **WHEN** 管理員已透過 API 新增模型並切換 active model
- **THEN** 重啟後 active model 維持 DB 中的設定

#### Scenario: Claude 模型定價欄位
- **WHEN** 查詢 Claude 模型
- **THEN** 每個模型有 `input`、`output`、`cache_write`、`cache_read` 定價（USD per million tokens）

#### Scenario: Gemini 模型定價欄位
- **WHEN** 查詢 Gemini 模型
- **THEN** 每個模型有 `text_input`、`audio_input`、`output`、`tokens_per_sec` 欄位

### Requirement: Gemini 音訊定價為 token-based 計算

`ExtendedUsageMonitor` SHALL 使用 token-based 公式計算 Gemini 音訊成本：`duration_sec × tokens_per_sec × price_per_token`，定價從 DB model_config 取得。

#### Scenario: 計算 gemini-2.0-flash 音訊成本
- **WHEN** 有一筆 30 秒 input 音訊紀錄（gemini-2.0-flash）
- **THEN** 成本為 `30 × 25 × 0.70 / 1_000_000`

#### Scenario: 計算 gemini-2.5-flash 音訊成本
- **WHEN** 有一筆 30 秒 input 音訊紀錄（gemini-2.5-flash）
- **THEN** 成本為 `30 × 25 × 1.00 / 1_000_000`

### Requirement: GET /api/models 列出所有模型

`GET /api/models` SHALL 回傳所有已註冊的模型及其定價資訊。

#### Scenario: 列出所有模型
- **WHEN** 呼叫 `GET /api/models`
- **THEN** 回傳所有模型（含 provider、model_id、display_name、is_active、pricing）

#### Scenario: 依 provider 篩選
- **WHEN** 呼叫 `GET /api/models?provider=claude`
- **THEN** 只回傳 Claude 模型

### Requirement: POST /api/models 新增模型

`POST /api/models` SHALL 新增模型配置，驗證必要欄位後存入 DB。

#### Scenario: 新增 Claude 模型
- **WHEN** 呼叫 `POST /api/models` 帶入完整的 Claude 模型資訊
- **THEN** 模型存入 DB
- **THEN** 回傳 201 + 新建的模型

#### Scenario: 新增重複 model_id
- **WHEN** 呼叫 `POST /api/models` 帶入已存在的 model_id
- **THEN** 回傳 409 錯誤

### Requirement: PUT /api/models/{model_id} 更新模型

`PUT /api/models/{model_id}` SHALL 更新模型的定價或 display_name。

#### Scenario: 更新定價
- **WHEN** 呼叫 `PUT /api/models/gemini-2.0-flash` 帶入新定價
- **THEN** DB 中該模型定價更新
- **THEN** 回傳更新後的模型

#### Scenario: 更新不存在的模型
- **WHEN** 呼叫 `PUT /api/models/nonexistent`
- **THEN** 回傳 404 錯誤

### Requirement: DELETE /api/models/{model_id} 刪除模型

`DELETE /api/models/{model_id}` SHALL 刪除模型配置，但不可刪除 active model。

#### Scenario: 刪除非 active 模型
- **WHEN** 呼叫 `DELETE /api/models/claude-haiku-4-20250514`（非 active）
- **THEN** 模型從 DB 移除
- **THEN** 回傳 204

#### Scenario: 刪除 active 模型
- **WHEN** 呼叫 `DELETE /api/models/claude-sonnet-4-20250514`（目前 active）
- **THEN** 回傳 409 錯誤
- **THEN** 模型不被刪除

### Requirement: GET /api/settings 回傳當前模型與可選清單

`GET /api/settings` SHALL 回傳當前使用的 Claude / Gemini active model ID，以及可選模型清單。

#### Scenario: 讀取設定
- **WHEN** 呼叫 `GET /api/settings`
- **THEN** 回傳 JSON 包含 `claude_model`、`gemini_model`（當前 active model ID）
- **THEN** 包含 `available_claude_models` 和 `available_gemini_models` 清單

### Requirement: PUT /api/settings 切換 active model

`PUT /api/settings` SHALL 接受 `claude_model` 和/或 `gemini_model` 欄位，驗證 model_id 存在於 DB 後切換 active model。

#### Scenario: 切換 Claude 模型
- **WHEN** 呼叫 `PUT /api/settings` 帶入 `{"claude_model": "claude-opus-4-20250514"}`
- **THEN** DB 中 `claude-opus-4-20250514` 的 `is_active` 設為 TRUE
- **THEN** 原本 active 的 Claude 模型 `is_active` 設為 FALSE
- **THEN** 回傳更新後的完整設定

#### Scenario: 切換到不存在的模型
- **WHEN** 呼叫 `PUT /api/settings` 帶入 `{"claude_model": "invalid-model"}`
- **THEN** 回傳 422 錯誤
- **THEN** active model 不變

### Requirement: agent_factory 使用 active model

`agent_factory` 建立 Agent 時 SHALL 使用 DB 中的 active Claude model，`ExtendedUsageMonitor.model` 同步為此值。

#### Scenario: Agent 使用 active Claude 模型
- **WHEN** DB 中 active Claude model 為 `'claude-opus-4-20250514'`
- **THEN** 新建的 Agent 使用該模型
- **THEN** `ExtendedUsageMonitor.model` 為 `'claude-opus-4-20250514'`

### Requirement: gemini_handler 使用 active model

`GeminiHandler` 建立 session 時 SHALL 使用 DB 中的 active Gemini model。

#### Scenario: Gemini session 使用 active 模型
- **WHEN** DB 中 active Gemini model 為 `'gemini-2.5-flash'`
- **THEN** 新建的 Gemini session 使用 `'gemini-2.5-flash'` 模型
