Feature: FastRTC 整合
  作為系統
  我想要將 GeminiHandler 透過 FastRTC Stream 掛載至 FastAPI app
  以便使用者可透過 WebRTC 進行即時語音對話

  Rule: Stream 掛載

    Scenario: App 啟動後 WebRTC endpoint 存在
      Given FastAPI app 已建立且 Stream 已掛載
      Then app 應包含 /api/conversation/rtc/webrtc/offer 路由

  Rule: Manager 與 Handler 串接

    Scenario: start_conversation 建立的 handler 帶有正確的 system_instruction
      Given ConversationManager 已初始化且 Stream 已掛載
      When 使用者啟動對話且 scenario_designer 回傳 "You are a hotel receptionist"
      Then handler 的 system_instruction 應為 "You are a hotel receptionist"
      And handler 的 gemini_client 應已設定

    Scenario: handler 斷線時 manager 收到通知並更新狀態
      Given ConversationManager 已初始化且有一個 active 對話
      When handler 的 on_disconnect 被觸發
      Then 對話狀態應轉為 failed
