Feature: 專案基礎架構

  Rule: 環境配置

    Scenario: 所有必要環境變數存在時正確建立 Settings
      Given 環境變數 DB_URL 設為 "postgresql://localhost/test"
      And 環境變數 ANTHROPIC_API_KEY 設為 "sk-test"
      And 環境變數 GEMINI_API_KEY 設為 "ai-test"
      When 建立 Settings 物件
      Then Settings 應包含正確的 db_url
      And Settings 應包含正確的 anthropic_api_key
      And Settings 應包含正確的 gemini_api_key

    Scenario: 缺少必要環境變數時拋出錯誤
      Given 環境變數 DB_URL 未設定
      When 嘗試建立 Settings 物件
      Then 應拋出 ValueError 並提示缺少 DB_URL

  Rule: FastAPI App

    Scenario: Health check 回傳正常狀態
      Given FastAPI app 已建立
      When 發送 GET 請求到 "/health"
      Then 回應狀態碼為 200
      And 回應內容包含 "status" 為 "ok"

    Scenario: Content router 已掛載
      Given FastAPI app 已建立
      When 發送 GET 請求到 "/api/content/health"
      Then 回應狀態碼為 200

    Scenario: Conversation router 已掛載
      Given FastAPI app 已建立
      When 發送 GET 請求到 "/api/conversation/health"
      Then 回應狀態碼為 200

    Scenario: Assessment router 已掛載
      Given FastAPI app 已建立
      When 發送 GET 請求到 "/api/assessment/health"
      Then 回應狀態碼為 200

    Scenario: Usage endpoint 回傳用量摘要
      Given FastAPI app 已建立
      When 發送 GET 請求到 "/api/usage"
      Then 回應狀態碼為 200
      And 回應內容包含欄位 "total_requests"
