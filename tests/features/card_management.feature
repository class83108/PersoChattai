Feature: 卡片管理
  作為使用者
  我想要建立、查詢學習素材卡片
  以便瀏覽和選擇 Role Play 對話的素材

  Background:
    Given 測試用 CardRepository 已初始化

  Rule: 建立卡片

    Scenario: 成功建立卡片
      When 建立卡片 title "Business Email" source_type "podcast_allearsenglish" summary "Learn email writing"
      Then 卡片成功寫入
      And 卡片包含自動產生的 id
      And 卡片包含 created_at

    Scenario: source_url 重複時不重複建立
      Given 已存在一張 source_url 為 "https://example.com/ep1" 的卡片
      When 建立卡片 source_url 為 "https://example.com/ep1"
      Then 不拋出錯誤
      And 資料庫中 source_url "https://example.com/ep1" 的卡片只有 1 筆

  Rule: 查詢卡片列表

    Scenario: 無篩選條件查詢
      Given 資料庫中有 3 張卡片
      When 查詢卡片列表不帶任何篩選條件
      Then 回傳 3 張卡片
      And 按 created_at DESC 排序

    Scenario: 依 source_type 篩選
      Given 資料庫中有 source_type "podcast_allearsenglish" 的卡片 2 張
      And 資料庫中有 source_type "user_pdf" 的卡片 1 張
      When 查詢卡片列表篩選 source_type "podcast_allearsenglish"
      Then 回傳 2 張卡片

    Scenario: 依 difficulty_level 篩選
      Given 資料庫中有 difficulty_level "B1" 的卡片 2 張
      And 資料庫中有 difficulty_level "C1" 的卡片 1 張
      When 查詢卡片列表篩選 difficulty "B1"
      Then 回傳 2 張卡片

    Scenario: 依 tag 篩選
      Given 資料庫中有包含 tag "business" 的卡片 1 張
      And 資料庫中有不包含 tag "business" 的卡片 2 張
      When 查詢卡片列表篩選 tag "business"
      Then 回傳 1 張卡片

    Scenario: 依關鍵字搜尋
      Given 資料庫中有 title 含 "Interview" 的卡片 1 張
      And 資料庫中有 summary 含 "interview tips" 的卡片 1 張
      And 資料庫中有不含 "interview" 的卡片 1 張
      When 查詢卡片列表篩選 keyword "interview"
      Then 回傳 2 張卡片

    Scenario: 多條件組合篩選
      Given 資料庫中有組合篩選卡片 source_type "podcast_allearsenglish" 且 difficulty "B1" 共 1 張
      And 資料庫中有組合篩選卡片 source_type "podcast_allearsenglish" 且 difficulty "C1" 共 1 張
      When 查詢卡片列表篩選 source_type "podcast_allearsenglish" 且 difficulty "B1"
      Then 回傳 1 張卡片

    Scenario: 分頁查詢
      Given 資料庫中有 10 張卡片
      When 查詢卡片列表 limit 3 offset 2
      Then 回傳 3 張卡片
      And 跳過前 2 張

    Scenario: 無任何卡片時查詢回傳空列表
      Given 資料庫中沒有任何卡片
      When 查詢卡片列表不帶任何篩選條件
      Then 回傳 0 張卡片

  Rule: 查詢單一卡片

    Scenario: 卡片存在
      Given 資料庫中有一張 id 為 "test-card-id" 的卡片
      When 查詢卡片 "test-card-id"
      Then 回傳該卡片的完整資料

    Scenario: 卡片不存在
      When 查詢卡片 "nonexistent-id"
      Then 回傳 None

  Rule: 卡片 API

    Scenario: GET /api/content/cards 回傳卡片列表
      Given 資料庫中有 2 張卡片
      When 發送 GET /api/content/cards
      Then API 回應狀態碼為 200
      And API 回應包含 2 張卡片

    Scenario: GET /api/content/cards/{card_id} 卡片存在
      Given 資料庫中有一張卡片
      When 發送 GET /api/content/cards/{card_id}
      Then API 回應狀態碼為 200
      And API 回應包含卡片完整欄位

    Scenario: GET /api/content/cards/{card_id} 卡片不存在
      When 發送 GET /api/content/cards/nonexistent-id
      Then API 回應狀態碼為 404

    Scenario: 卡片回傳 JSON 符合 Card schema
      Given 資料庫中有一張包含 keywords 和 tags 的卡片
      When 發送 GET /api/content/cards/{card_id}
      Then API 回應包含 id, title, summary, source_type, keywords, tags, difficulty_level, created_at
