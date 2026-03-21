Feature: 模型切換 API
  作為 PersoChattai 管理員
  我想要 透過 API 讀取與切換 active model
  以便 從前端切換 Claude 和 Gemini 的使用模型

  Background:
    Given DB 已 seed 預設模型配置

  Rule: 讀取設定

    Scenario: GET /api/settings 回傳 active model 與可選清單
      When 呼叫 GET /api/settings
      Then 回傳 200
      And response 包含 "claude_model" 為目前 active Claude model ID
      And response 包含 "gemini_model" 為目前 active Gemini model ID
      And response 包含 "available_claude_models" 清單
      And response 包含 "available_gemini_models" 清單

  Rule: 切換 active model

    Scenario: PUT /api/settings 切換 Claude 模型
      When 呼叫 PUT /api/settings 帶入 {"claude_model": "claude-opus-4-20250514"}
      Then 回傳 200
      And response 的 "claude_model" 為 "claude-opus-4-20250514"
      And 再次 GET /api/settings 確認 "claude_model" 為 "claude-opus-4-20250514"

    Scenario: PUT /api/settings 切換 Gemini 模型
      When 呼叫 PUT /api/settings 帶入 {"gemini_model": "gemini-2.5-flash"}
      Then 回傳 200
      And response 的 "gemini_model" 為 "gemini-2.5-flash"

    Scenario: PUT /api/settings 同時切換兩個 provider
      When 呼叫 PUT /api/settings 帶入 {"claude_model": "claude-opus-4-20250514", "gemini_model": "gemini-2.5-flash"}
      Then 回傳 200
      And response 的 "claude_model" 為 "claude-opus-4-20250514"
      And response 的 "gemini_model" 為 "gemini-2.5-flash"

    Scenario: PUT /api/settings 部分更新只帶一個 provider
      When 呼叫 PUT /api/settings 帶入 {"claude_model": "claude-opus-4-20250514"}
      Then 回傳 200
      And response 的 "gemini_model" 仍為原本的 active model

  Rule: 錯誤處理

    Scenario: PUT /api/settings 不存在的 model_id
      When 呼叫 PUT /api/settings 帶入 {"claude_model": "invalid-model"}
      Then 回傳 422
      And active model 不變

    Scenario: PUT /api/settings 空 body
      When 呼叫 PUT /api/settings 帶入空 body
      Then 回傳 422

  Rule: 切換冪等性

    Scenario: 切換到已經是 active 的 model
      Given Claude 的 active model 是 "claude-sonnet-4-20250514"
      When 呼叫 PUT /api/settings 帶入 {"claude_model": "claude-sonnet-4-20250514"}
      Then 回傳 200
      And active model 仍為 "claude-sonnet-4-20250514"

  Rule: DB 為空時使用 Settings fallback

    Scenario: DB 無 active model 時回傳 Settings 預設值
      Given model_config table 為空
      When 呼叫 GET /api/settings
      Then 回傳 200
      And response 的 "claude_model" 為 Settings 的 claude_model 預設值
      And response 的 "gemini_model" 為 Settings 的 gemini_model 預設值
