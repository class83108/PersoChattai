Feature: 評估歷史與成長追蹤
  作為使用者
  我想要查詢過去的評估結果和詞彙成長
  以便了解自己的英文能力進步狀況

  Background:
    Given 測試用 AssessmentRepository 已初始化

  Rule: 評估記錄 CRUD

    Scenario: 建立評估記錄
      When 建立 assessment 記錄含完整欄位
      Then assessment 成功寫入
      And assessment 包含自動產生的 id
      And assessment 包含 created_at

    Scenario: 查詢單一評估
      Given 資料庫中有一筆 assessment 記錄
      When 查詢該 assessment
      Then 回傳完整的評估資料含量化指標和質性分析

    Scenario: 查詢使用者評估歷史
      Given 使用者有 5 筆 assessment 記錄
      When 查詢該使用者的評估歷史 limit 3 offset 0
      Then 回傳 3 筆記錄
      And 按 created_at DESC 排序

  Rule: 詞彙庫管理

    Scenario: 新增詞彙
      When 呼叫 upsert_words 新增 ["pragmatic", "nuanced"]
      Then user_vocabulary 新增 2 筆記錄
      And 每筆 occurrence_count 為 1
      And 每筆包含 first_seen_at 和 first_seen_conversation_id

    Scenario: 已知詞彙累加
      Given 使用者詞彙庫中已有 "pragmatic" occurrence_count 為 2
      When 呼叫 upsert_words 新增 ["pragmatic"]
      Then "pragmatic" 的 occurrence_count 變為 3

    Scenario: 查詢詞彙統計
      Given 使用者詞彙庫中有 50 個詞彙
      When 查詢詞彙統計
      Then 回傳 total_words 為 50
      And 回傳 recent_words 列表

  Rule: Level Snapshot

    Scenario: 建立 snapshot
      When 建立 level_snapshot 含 cefr_level "B1" 和聚合指標
      Then snapshot 成功寫入

    Scenario: 查詢最新 snapshot
      Given 使用者有 3 個 level_snapshot
      When 查詢最新 snapshot
      Then 回傳最近一個 snapshot

    Scenario: 查詢 snapshot 歷史
      Given 使用者有 3 個 level_snapshot
      When 查詢 snapshot 歷史 limit 2
      Then 回傳 2 筆 snapshot
      And 按日期 DESC 排序

  Rule: REST API

    Scenario: GET /api/assessment/{id} 評估存在
      Given 資料庫中有一筆 assessment 記錄
      When 發送 GET /api/assessment/{assessment_id}
      Then API 回應狀態碼為 200
      And 回應包含完整評估資料

    Scenario: GET /api/assessment/{id} 評估不存在
      When 發送 GET /api/assessment/nonexistent-id
      Then API 回應狀態碼為 404

    Scenario: GET /api/assessment/user/{id}/history 查詢歷史
      Given 使用者有 3 筆 assessment 記錄
      When 發送 GET /api/assessment/user/{user_id}/history?limit=2
      Then API 回應狀態碼為 200
      And 回應包含 2 筆評估記錄

    Scenario: GET /api/assessment/user/{id}/vocabulary 查詢詞彙
      Given 使用者詞彙庫中有 10 個詞彙
      When 發送 GET /api/assessment/user/{user_id}/vocabulary
      Then API 回應狀態碼為 200
      And 回應包含 total_words 和 recent_words

    Scenario: GET /api/assessment/user/{id}/progress 查詢成長
      Given 使用者有評估記錄和 level_snapshot
      When 發送 GET /api/assessment/user/{user_id}/progress
      Then API 回應狀態碼為 200
      And 回應包含最新 snapshot 和最近評估摘要

  Rule: 錯誤處理

    Scenario: 查詢不存在使用者的歷史
      When 發送 GET /api/assessment/user/nonexistent-user/history
      Then API 回應狀態碼為 200
      And 回應為空列表

    Scenario: 新使用者查詢成長追蹤
      When 發送 GET /api/assessment/user/new-user/progress
      Then API 回應狀態碼為 200
      And snapshot 為 null
      And assessments 為空列表

  Rule: 輸入邊界

    Scenario: 分頁 offset 超出範圍
      Given 使用者有 2 筆 assessment 記錄
      When 查詢該使用者的評估歷史 limit 10 offset 100
      Then 回傳空列表

    Scenario: 詞彙庫為空時查詢統計
      When 查詢詞彙統計
      Then 回傳 total_words 為 0
      And 回傳 recent_words 為空列表

  Rule: get_user_history Tool

    Scenario: Agent 查詢使用者完整歷史
      Given 使用者有評估記錄、詞彙庫和 level_snapshot
      When Agent 呼叫 get_user_history
      Then 回傳最新 level_snapshot
      And 回傳最近 5 次 assessment 摘要
      And 回傳詞彙統計

    Scenario: 新使用者無歷史
      When Agent 呼叫 get_user_history 查詢新使用者
      Then snapshot 為 null
      And assessments 為空列表
      And total_words 為 0

  Rule: 輸出契約

    Scenario: API 回傳 JSON 包含完整 assessment 欄位
      Given 資料庫中有一筆完整的 assessment 記錄
      When 發送 GET /api/assessment/{assessment_id}
      Then 回應包含 id conversation_id user_id cefr_level
      And 回應包含 mtld vocd_d k1_ratio k2_ratio awl_ratio
      And 回應包含 lexical_assessment fluency_assessment grammar_assessment
      And 回應包含 suggestions new_words created_at

    Scenario: progress API 回傳結構正確
      Given 使用者有評估記錄和 level_snapshot
      When 發送 GET /api/assessment/user/{user_id}/progress
      Then 回應包含 snapshot 物件含 cefr_level avg_mtld vocabulary_size
      And 回應包含 recent_assessments 列表
