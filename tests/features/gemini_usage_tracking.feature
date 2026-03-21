Feature: Gemini 音訊用量追蹤
  作為 PersoChattai 系統
  我想要 追蹤 Gemini Live API 的音訊用量與成本
  以便 了解語音對話的 API 花費

  Rule: ExtendedUsageMonitor 繼承 UsageMonitor

    Scenario: 繼承後仍可追蹤 token 使用量
      Given 一個 ExtendedUsageMonitor 實例
      When 呼叫 record() 傳入含 100 input_tokens 和 50 output_tokens 的 usage
      Then records 新增一筆 UsageRecord
      And input_tokens 為 100 且 output_tokens 為 50

    Scenario: ExtendedUsageMonitor 是 UsageMonitor 的子類別
      Given 一個 ExtendedUsageMonitor 實例
      Then isinstance 檢查 UsageMonitor 為 True

  Rule: 記錄 Gemini 音訊用量

    Scenario: 記錄一筆 input 音訊
      Given 一個 ExtendedUsageMonitor 實例
      When 呼叫 record_audio 帶入 duration_sec 30.5 和 direction "input" 和 model "gemini-2.0-flash"
      Then audio_records 新增一筆紀錄
      And audio_duration_sec 為 30.5 且 direction 為 "input"

    Scenario: 監控停用時不記錄音訊
      Given 一個停用的 ExtendedUsageMonitor 實例
      When 呼叫 record_audio 帶入 duration_sec 10.0 和 direction "input" 和 model "gemini-2.0-flash"
      Then audio_records 為空列表
      And record_audio 回傳 None

    Scenario: 零秒音訊仍可記錄
      Given 一個 ExtendedUsageMonitor 實例
      When 呼叫 record_audio 帶入 duration_sec 0.0 和 direction "input" 和 model "gemini-2.0-flash"
      Then audio_records 新增一筆紀錄
      And audio_duration_sec 為 0.0 且 direction 為 "input"

  Rule: GeminiAudioRecord 資料結構

    Scenario: 序列化為 dict
      Given 一筆 GeminiAudioRecord 紀錄 duration 10.0 direction "output" model "gemini-2.0-flash"
      When 呼叫 to_dict()
      Then 回傳包含 "timestamp" 和 "audio_duration_sec" 和 "direction" 和 "model"
      And "audio_duration_sec" 值為 10.0

  Rule: Gemini 音訊定價計算

    Scenario: 已知模型的音訊成本
      Given 一個 ExtendedUsageMonitor 實例
      And 已記錄一筆 gemini-2.0-flash input 音訊 30 秒
      When 計算 gemini 音訊總成本
      Then 成本等於 30 乘以 gemini-2.0-flash 的 input_per_second

    Scenario: 未知模型使用預設定價
      Given 一個 ExtendedUsageMonitor 實例
      And 已記錄一筆 unknown-model input 音訊 10 秒
      When 計算 gemini 音訊總成本
      Then 成本等於 10 乘以預設 input_per_second

  Rule: get_summary 包含 Gemini 成本

    Scenario: 有 token 和音訊紀錄的 summary
      Given 一個 ExtendedUsageMonitor 實例
      And 已記錄 2 筆 token 紀錄
      And 已記錄 3 筆音訊紀錄
      When 呼叫 get_summary()
      Then summary 包含 "tokens" 區塊
      And summary 包含 "cost_estimate_usd" 區塊
      And summary 包含 "gemini_audio" 區塊
      And gemini_audio 的 total_requests 為 3

    Scenario: 只有 audio 無 token 的 summary
      Given 一個 ExtendedUsageMonitor 實例
      And 已記錄 2 筆音訊紀錄
      When 呼叫 get_summary()
      Then summary 包含 "gemini_audio" 區塊
      And gemini_audio 的 total_requests 為 2
      And total_requests 為 0

    Scenario: 無任何紀錄的 summary
      Given 一個 ExtendedUsageMonitor 實例
      When 呼叫 get_summary()
      Then total_requests 為 0
      And 回傳包含 "message" 欄位
      And gemini_audio 的 total_requests 為 0
