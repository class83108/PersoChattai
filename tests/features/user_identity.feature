Feature: 使用者識別
  作為使用者
  我想要透過暱稱建立身份
  以便系統能追蹤我的學習歷史與對話記錄

  Background:
    Given 測試用資料庫已初始化

  Rule: 建立使用者

    Scenario: 以新暱稱建立使用者
      When 發送 POST /api/users，display_name 為 "小明"
      Then 回應狀態碼為 201
      And 回應包含 id 為合法 UUID
      And 回應包含 display_name 為 "小明"

    Scenario: 以既有暱稱回傳使用者
      Given 已存在暱稱為 "小明" 的使用者
      When 發送 POST /api/users，display_name 為 "小明"
      Then 回應狀態碼為 200
      And 回應包含的 id 與既有使用者相同

    Scenario: 重複 POST 同暱稱不會產生多筆 user
      When 發送 POST /api/users，display_name 為 "小華" 兩次
      Then 兩次回應的 id 相同
      And 資料庫中 display_name 為 "小華" 的 user 僅有一筆

  Rule: 暱稱格式驗證

    Scenario: display_name 為空字串
      When 發送 POST /api/users，display_name 為空字串
      Then 回應狀態碼為 422

    Scenario: display_name 超過 20 字
      When 發送 POST /api/users，display_name 為 21 個字的字串
      Then 回應狀態碼為 422

    Scenario: display_name 恰好 1 字
      When 發送 POST /api/users，display_name 為 "A"
      Then 回應狀態碼為 201

    Scenario: display_name 恰好 20 字
      When 發送 POST /api/users，display_name 為 20 個字的字串
      Then 回應狀態碼為 201

    Scenario: display_name 前後空白自動 trim
      When 發送 POST /api/users，display_name 為 "  小明  "
      Then 回應狀態碼為 201
      And 回應包含 display_name 為 "小明"

    Scenario: trim 後為空字串
      When 發送 POST /api/users，display_name 為 "   "
      Then 回應狀態碼為 422

  Rule: 查詢使用者

    Scenario: 查詢存在的使用者
      Given 已存在暱稱為 "小明" 的使用者
      When 以該使用者的 id 發送 GET /api/users/{user_id}
      Then 回應狀態碼為 200
      And 回應包含 id
      And 回應包含 display_name 為 "小明"
      And 回應包含 current_level

    Scenario: 查詢不存在的使用者
      When 以不存在的 UUID 發送 GET /api/users/{user_id}
      Then 回應狀態碼為 404

    Scenario: user_id 格式非 UUID
      When 以 "not-a-uuid" 發送 GET /api/users/{user_id}
      Then 回應狀態碼為 422

  Rule: 特殊字元與 Edge Cases

    Scenario: display_name 含 emoji
      When 發送 POST /api/users，display_name 為 "學霸🎓"
      Then 回應狀態碼為 201
      And 回應包含 display_name 為 "學霸🎓"

    Scenario: display_name 含特殊字元
      When 發送 POST /api/users，display_name 為 "user@#$"
      Then 回應狀態碼為 201

  Rule: 回應格式契約

    Scenario: POST 201 回應格式
      When 發送 POST /api/users，display_name 為 "契約測試"
      Then 回應狀態碼為 201
      And 回應 JSON 僅包含 id 和 display_name 欄位

    Scenario: GET 200 回應格式
      Given 已存在暱稱為 "契約測試" 的使用者
      When 以該使用者的 id 發送 GET /api/users/{user_id}
      Then 回應狀態碼為 200
      And 回應 JSON 包含 id、display_name、current_level 欄位
