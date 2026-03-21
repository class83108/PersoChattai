Feature: 模型配置 Repository
  作為 PersoChattai 系統
  我想要 在 DB 中管理可選模型與定價配置
  以便 管理員可新增、修改、刪除模型且重啟不遺失

  Rule: 啟動時 seed 預設模型

    Scenario: table 為空時自動 seed
      Given 一個空的 model_config table
      When 執行 seed 邏輯
      Then DB 有 3 筆 Claude 模型（sonnet, opus, haiku）
      And DB 有 2 筆 Gemini 模型（2.0-flash, 2.5-flash）
      And 每個 provider 各有一個 is_active 為 TRUE 的模型

    Scenario: table 已有資料時不重複 seed
      Given model_config table 已有 1 筆 Claude 模型
      When 執行 seed 邏輯
      Then DB 仍然只有 1 筆 Claude 模型

  Rule: CRUD 正常操作

    Scenario: 列出所有模型
      Given DB 有預設的 5 筆模型配置
      When 呼叫 list_models()
      Then 回傳 5 筆 ModelConfig

    Scenario: 依 provider 篩選
      Given DB 有預設的 5 筆模型配置
      When 呼叫 list_models(provider="claude")
      Then 回傳 3 筆 ModelConfig
      And 每筆的 provider 都是 "claude"

    Scenario: 取得 active model
      Given DB 有預設的 5 筆模型配置
      When 呼叫 get_active_model(provider="claude")
      Then 回傳 is_active 為 TRUE 的 Claude 模型

    Scenario: 新增模型
      Given DB 有預設的 5 筆模型配置
      When 呼叫 create_model 帶入一筆新的 Gemini 模型
      Then DB 多一筆模型紀錄
      And 回傳的 ModelConfig 包含完整欄位

    Scenario: 更新模型定價
      Given DB 有預設的 5 筆模型配置
      When 呼叫 update_model 更新 "gemini-2.0-flash" 的 pricing
      Then DB 中該模型的 pricing 已更新
      And updated_at 時間已更新

    Scenario: 刪除非 active 模型
      Given DB 有預設的 5 筆模型配置
      And "claude-haiku-4-20250514" 不是 active 模型
      When 呼叫 delete_model("claude-haiku-4-20250514")
      Then DB 剩 4 筆模型

  Rule: 切換 active model

    Scenario: 切換 active model 同時更新新舊狀態
      Given DB 有預設的 5 筆模型配置
      And Claude 的 active model 是 "claude-sonnet-4-20250514"
      When 呼叫 set_active_model(provider="claude", model_id="claude-opus-4-20250514")
      Then "claude-opus-4-20250514" 的 is_active 為 TRUE
      And "claude-sonnet-4-20250514" 的 is_active 為 FALSE

    Scenario: 切換到已經是 active 的 model（冪等）
      Given DB 有預設的 5 筆模型配置
      And Claude 的 active model 是 "claude-sonnet-4-20250514"
      When 呼叫 set_active_model(provider="claude", model_id="claude-sonnet-4-20250514")
      Then "claude-sonnet-4-20250514" 的 is_active 仍為 TRUE

  Rule: 錯誤處理

    Scenario: 新增重複 model_id
      Given DB 有預設的 5 筆模型配置
      When 呼叫 create_model 帶入已存在的 model_id "claude-sonnet-4-20250514"
      Then 拋出 DuplicateModelError

    Scenario: 刪除 active 模型
      Given DB 有預設的 5 筆模型配置
      And "claude-sonnet-4-20250514" 是 active 模型
      When 呼叫 delete_model("claude-sonnet-4-20250514")
      Then 拋出 ActiveModelDeleteError

    Scenario: 更新不存在的模型
      Given DB 有預設的 5 筆模型配置
      When 呼叫 update_model("nonexistent-model", ...)
      Then 拋出 ModelNotFoundError

    Scenario: 切換到不存在的 model_id
      Given DB 有預設的 5 筆模型配置
      When 呼叫 set_active_model(provider="claude", model_id="nonexistent")
      Then 拋出 ModelNotFoundError

  Rule: 輸出格式

    Scenario: ModelConfig 包含完整欄位
      Given DB 有預設的 5 筆模型配置
      When 呼叫 list_models() 取得第一筆
      Then ModelConfig 有 id, provider, model_id, display_name, is_active, pricing 欄位

    Scenario: Claude 模型 pricing 包含必要定價欄位
      Given DB 有預設的 5 筆模型配置
      When 查詢 "claude-sonnet-4-20250514" 的 pricing
      Then pricing 包含 "input", "output", "cache_write", "cache_read" 欄位

    Scenario: Gemini 模型 pricing 包含必要定價欄位
      Given DB 有預設的 5 筆模型配置
      When 查詢 "gemini-2.0-flash" 的 pricing
      Then pricing 包含 "text_input", "audio_input", "output", "tokens_per_sec" 欄位
