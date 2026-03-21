Feature: 素材輸入
  作為使用者
  我想要上傳 PDF 或輸入自由主題
  以便產生學習素材卡片進行對話練習

  Background:
    Given 測試用 ContentService 已初始化

  Rule: PDF 上傳

    Scenario: 成功上傳並解析 PDF
      Given 一個有效的 PDF 檔案大小 1MB 含文字 "English learning tips"
      When 發送 POST /api/content/upload-pdf 上傳該 PDF
      Then 回應狀態碼為 200
      And 回應包含產出的卡片列表

    Scenario: 檔案超過大小限制
      Given 一個 PDF 檔案大小 15MB
      When 發送 POST /api/content/upload-pdf 上傳該 PDF
      Then 回應狀態碼為 413
      And 回應訊息包含 "檔案過大，請上傳 10MB 以下的 PDF"

    Scenario: 文字內容超過長度限制時自動截斷
      Given 一個有效的 PDF 檔案含 8000 字的文字
      When 發送 POST /api/content/upload-pdf 上傳該 PDF
      Then 回應狀態碼為 200
      And 回應包含截斷提示
      And 實際處理的文字不超過 5000 字

    Scenario: PDF 無法解析文字
      Given 一個純圖片 PDF 檔案
      When 發送 POST /api/content/upload-pdf 上傳該 PDF
      Then 回應狀態碼為 422
      And 回應訊息包含 "無法讀取此 PDF，請確認檔案包含文字內容"

    Scenario: 截斷在句子邊界
      Given 一個有效的 PDF 檔案含超過 5000 字的文字
      When ContentService 截斷文字至 5000 字
      Then 截斷位置在句子結尾（句號、問號、驚嘆號之後）

  Rule: 自由主題

    Scenario: 成功建立自由主題卡片
      Given 主題描述 "I want to practice ordering food at a restaurant"
      When 發送 POST /api/content/free-topic
      Then 回應狀態碼為 200
      And 回應包含產出的卡片

    Scenario: 主題描述過長
      Given 主題描述超過 500 字
      When 發送 POST /api/content/free-topic
      Then 回應狀態碼為 422
      And 回應包含驗證錯誤

    Scenario: 主題描述為空
      Given 主題描述為空字串
      When 發送 POST /api/content/free-topic
      Then 回應狀態碼為 422

    Scenario: 主題描述恰好 500 字
      Given 主題描述恰好 500 字
      When 發送 POST /api/content/free-topic
      Then 回應狀態碼為 200

  Rule: PDF 輸入邊界

    Scenario: PDF 文字恰好 5000 字不截斷
      Given 一個有效的 PDF 檔案含恰好 5000 字的文字
      When ContentService 處理該 PDF
      Then 不觸發截斷
      And 完整文字送入摘要 pipeline

    Scenario: PDF 只有 1 個字
      Given 一個有效的 PDF 檔案含 1 個字的文字
      When ContentService 處理該 PDF
      Then 完整文字送入摘要 pipeline

  Rule: 上傳後卡片寫入 DB

    Scenario: PDF 上傳後卡片正確寫入 DB
      Given 一個有效的 PDF 檔案
      When 上傳並摘要完成
      Then 卡片記錄存在於 cards 表
      And 卡片 source_type 為 "user_pdf"

    Scenario: 自由主題卡片正確寫入 DB
      Given 主題描述 "Discussing climate change"
      When 提交自由主題並摘要完成
      Then 卡片記錄存在於 cards 表
      And 卡片 source_type 為 "user_prompt"
