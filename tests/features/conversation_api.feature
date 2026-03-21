Feature: 對話 API
  作為使用者
  我想要透過 API 建立、查詢、結束語音對話
  以便進行英文 Role Play 練習並追蹤對話歷史

  Background:
    Given 測試用 ConversationManager 已初始化

  Rule: 建立對話

    Scenario: 成功建立對話
      Given 使用者 "user-1" 沒有進行中的對話
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 建立對話
      Then 回應狀態碼為 201
      And 回應包含 conversation_id
      And 回應包含 status 為 "preparing"

    Scenario: 缺少必要欄位時回傳 422
      When 發送建立對話請求但缺少 user_id
      Then 回應狀態碼為 422

    Scenario: source_type 不在允許值時回傳 422
      When 使用者 "user-1" 以 source_type "invalid_type" 和 source_ref "ref-1" 建立對話
      Then 回應狀態碼為 422

    Scenario: source_ref 為空時回傳 422
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "" 建立對話
      Then 回應狀態碼為 422

    Scenario: 已有進行中的對話時回傳 409
      Given 使用者 "user-1" 已有一個 active 對話
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-xyz" 建立對話
      Then 回應狀態碼為 409

    Scenario: ConversationManager 內部失敗時回傳 500
      Given ConversationManager 的 start_conversation 會拋出例外
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 建立對話
      Then 回應狀態碼為 500

  Rule: 查詢對話狀態

    Scenario: 查詢存在的對話
      Given 使用者 "user-1" 已建立一個對話
      When 查詢該對話的狀態
      Then 回應狀態碼為 200
      And 回應包含 conversation_id
      And 回應包含 status
      And 回應包含 started_at

    Scenario: 查詢不存在的對話回傳 404
      When 以不存在的 conversation_id 查詢對話狀態
      Then 回應狀態碼為 404

    Scenario: conversation_id 格式不合法回傳 422
      When 以 "not-a-uuid" 查詢對話狀態
      Then 回應狀態碼為 422

  Rule: 結束對話

    Scenario: 結束進行中的對話
      Given 使用者 "user-1" 有一個 active 對話
      When 結束該對話
      Then 回應狀態碼為 200
      And 回應包含 status 為 "assessing"

    Scenario: 結束非 active 對話回傳 409
      Given 使用者 "user-1" 有一個 completed 對話
      When 結束該對話
      Then 回應狀態碼為 409

    Scenario: 結束不存在的對話回傳 404
      When 以不存在的 conversation_id 結束對話
      Then 回應狀態碼為 404

  Rule: 對話歷史

    Scenario: 列出對話歷史
      Given 使用者 "user-1" 有 3 筆對話記錄
      When 查詢使用者 "user-1" 的對話歷史
      Then 回應狀態碼為 200
      And 回應包含 3 筆對話摘要
      And 每筆摘要包含 id、status、started_at、ended_at、source_type
      And 結果按 started_at 降序排列

    Scenario: 無對話歷史回傳空陣列
      When 查詢使用者 "user-no-history" 的對話歷史
      Then 回應狀態碼為 200
      And 回應為空陣列

    Scenario: user_id 格式不合法回傳 422
      When 以 "not-a-uuid" 查詢對話歷史
      Then 回應狀態碼為 422

  Rule: 跨 endpoint 狀態一致性

    Scenario: 建立對話後可透過查詢 API 取得
      When 使用者 "user-1" 以 source_type "free_topic" 和 source_ref "travel" 建立對話
      And 以回應中的 conversation_id 查詢對話狀態
      Then 回應包含 status 為 "preparing"

    Scenario: 結束對話後狀態反映在查詢與歷史中
      Given 使用者 "user-1" 有一個 active 對話
      When 結束該對話
      And 查詢該對話的狀態
      Then 回應包含 status 為 "assessing"
