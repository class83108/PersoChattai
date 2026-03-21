Feature: 內容摘要 Pipeline
  作為系統
  我想要將原始文字內容透過 Claude Agent 轉換為標準化卡片
  以便提供結構化的學習素材

  Background:
    Given 測試用 ContentService 已初始化
    And 模擬 Claude Agent 回傳有效的摘要結果

  Rule: 摘要 Happy Path

    Scenario: Podcast 文章摘要成功
      Given 一篇 Podcast 文章 source_type "podcast_allearsenglish" title "Business Email" content "Learn how to write professional emails..."
      When 呼叫 summarize_article
      Then 產出至少 1 張卡片
      And 每張卡片包含 title summary keywords difficulty_level tags
      And 卡片 source_type 為 "podcast_allearsenglish"

    Scenario: PDF 內容摘要成功
      Given PDF 文字內容 "Tips for job interviews..."
      When 呼叫 summarize_pdf
      Then 產出至少 1 張卡片
      And 卡片儲存至 DB

    Scenario: 自由主題展開成功
      Given 主題描述 "Ordering food at a restaurant"
      When 呼叫 summarize_free_topic
      Then 產出 1 張卡片
      And 卡片 source_type 為 "user_prompt"
      And 卡片儲存至 DB

  Rule: 摘要失敗處理

    Scenario: Claude Agent 呼叫失敗
      Given 模擬 Claude Agent 拋出例外
      When 呼叫 summarize_article
      Then 記錄 error log
      And 拋出明確的錯誤訊息
      And 不建立任何卡片

    Scenario: Claude Agent 回傳非預期格式
      Given 模擬 Claude Agent 回傳無法解析的格式
      When 呼叫 summarize_article
      Then 記錄 error log
      And 拋出明確的錯誤訊息
      And 不建立任何卡片

  Rule: 多卡片與 Edge Cases

    Scenario: 單篇素材產出多張卡片
      Given 模擬 Claude Agent 回傳 3 張卡片的摘要結果
      When 呼叫 summarize_article
      Then 產出 3 張卡片
      And 所有卡片共用相同的 source_url

    Scenario: 內容極短時仍能產出卡片
      Given 一篇 Podcast 文章 content 只有 "Hello world"
      When 呼叫 summarize_article
      Then 產出至少 1 張卡片

  Rule: 卡片寫入正確性

    Scenario: 摘要後卡片正確寫入 DB
      Given 一篇 Podcast 文章
      When 呼叫 summarize_article
      Then 所有產出的卡片都存在於 cards 表
      And 每張卡片的 source_url 與原始文章 URL 一致

    Scenario: 失敗時不建立部分卡片
      Given 模擬 Claude Agent 回傳 2 張卡片但第 2 張格式錯誤
      When 呼叫 summarize_article
      Then 不建立任何卡片

  Rule: 輸出契約

    Scenario: 卡片包含完整的 keywords 結構
      Given 模擬 Claude Agent 回傳含 keywords 的摘要
      When 呼叫 summarize_article
      Then 每張卡片的 keywords 包含 word definition example 欄位

    Scenario: 卡片 difficulty_level 為有效 CEFR 等級
      Given 模擬 Claude Agent 回傳摘要
      When 呼叫 summarize_article
      Then 每張卡片的 difficulty_level 為 A1 A2 B1 B2 C1 C2 其中之一
