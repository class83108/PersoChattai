Feature: App 啟動與服務初始化
  作為系統管理員
  我想要 App 啟動時正確初始化所有服務
  以便系統能完整運作

  Rule: Lifespan 服務初始化

    Scenario: App 啟動後所有服務存入 app.state
      Given 完整配置的 Settings
      When App 啟動完成 lifespan
      Then app.state 應包含 conversation_manager
      And app.state 應包含 model_config_repo
      And app.state 應包含 content_scheduler

    Scenario: ConversationManager 注入正確依賴
      Given 完整配置的 Settings
      When App 啟動完成 lifespan
      Then conversation_manager 應具備 repository
      And conversation_manager 應具備 scenario_designer
      And conversation_manager 應具備 assessment_service

    Scenario: ContentScheduler 在啟動時開始執行
      Given 完整配置的 Settings
      When App 啟動完成 lifespan
      Then content_scheduler 應處於 running 狀態
      And content_scheduler 應有 scrape_podcasts job

  Rule: Lifespan Shutdown

    Scenario: App 關閉時 ContentScheduler 停止
      Given App 已啟動且 ContentScheduler 正在運行
      When App 執行 shutdown
      Then content_scheduler 應處於非 running 狀態

    Scenario: App 關閉時 DB pool 已關閉
      Given App 已啟動
      When App 執行 shutdown
      Then DB pool 應已關閉

  Rule: FastRTC 掛載

    Scenario: WebRTC stream 路徑可用
      Given 完整配置的 Settings
      When App 啟動完成 lifespan
      Then 路徑 "/api/conversation/rtc" 應已註冊在 app routes 中

  Rule: 入口點

    Scenario: __main__ 模組可匯入
      When 匯入 persochattai.__main__ 模組
      Then 模組應包含啟動邏輯
