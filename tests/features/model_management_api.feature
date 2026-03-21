Feature: 模型管理 API
  作為 PersoChattai 管理員
  我想要 透過 API 管理可選模型與定價
  以便 新增模型或更新定價時不需要改 code

  Background:
    Given DB 已 seed 預設模型配置

  Rule: 列出模型

    Scenario: GET /api/models 列出所有模型
      When 呼叫 GET /api/models
      Then 回傳 200
      And response 包含 5 筆模型
      And 每筆包含 provider, model_id, display_name, is_active, pricing

    Scenario: GET /api/models?provider=claude 篩選
      When 呼叫 GET /api/models?provider=claude
      Then 回傳 200
      And response 只包含 provider 為 "claude" 的模型

  Rule: 新增模型

    Scenario: POST /api/models 新增 Claude 模型
      When 呼叫 POST /api/models 帶入新的 Claude 模型資訊
      Then 回傳 201
      And response 包含新建的模型完整資訊

    Scenario: POST /api/models 重複 model_id
      When 呼叫 POST /api/models 帶入已存在的 model_id
      Then 回傳 409

    Scenario: POST /api/models 缺少必要欄位
      When 呼叫 POST /api/models 缺少 pricing 欄位
      Then 回傳 422

  Rule: 更新模型

    Scenario: PUT /api/models/{model_id} 更新定價
      When 呼叫 PUT /api/models/gemini-2.0-flash 帶入新定價
      Then 回傳 200
      And response 中 pricing 為更新後的值

    Scenario: PUT /api/models/{model_id} 不存在的模型
      When 呼叫 PUT /api/models/nonexistent
      Then 回傳 404

  Rule: 刪除模型

    Scenario: DELETE /api/models/{model_id} 刪除非 active 模型
      When 呼叫 DELETE /api/models/claude-haiku-4-20250514
      Then 回傳 204
      And 再次 GET /api/models 不包含該模型

    Scenario: DELETE /api/models/{model_id} 刪除 active 模型
      When 呼叫 DELETE /api/models/claude-sonnet-4-20250514
      Then 回傳 409
      And 模型未被刪除
