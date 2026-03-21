Feature: API 使用紀錄持久化
  作為 PersoChattai 系統
  我想要 將 API 使用紀錄持久化到 PostgreSQL
  以便 重啟後不遺失用量資料

  Rule: UsageRepository 寫入紀錄

    Scenario: 寫入 token 紀錄
      Given 一個 mock DB pool 的 UsageRepository
      When 呼叫 save_token_record 帶入一筆 UsageRecord 和 model "claude-sonnet-4-20250514"
      Then DB 收到一筆 usage_type "token" 的 INSERT
      And 包含正確的 input_tokens 和 output_tokens

    Scenario: 寫入 audio 紀錄
      Given 一個 mock DB pool 的 UsageRepository
      When 呼叫 save_audio_record 帶入一筆 GeminiAudioRecord
      Then DB 收到一筆 usage_type "audio" 的 INSERT
      And 包含正確的 audio_duration_sec 和 direction

  Rule: UsageRepository 載入歷史紀錄

    Scenario: 載入 token 歷史紀錄
      Given 一個 mock DB pool 的 UsageRepository
      And DB 有 2 筆 token 紀錄
      When 呼叫 load_token_records(days=30)
      Then 回傳 2 筆 UsageRecord

    Scenario: 載入 audio 歷史紀錄
      Given 一個 mock DB pool 的 UsageRepository
      And DB 有 3 筆 audio 紀錄
      When 呼叫 load_audio_records(days=30)
      Then 回傳 3 筆 GeminiAudioRecord

    Scenario: 無歷史紀錄時回傳空列表
      Given 一個 mock DB pool 的 UsageRepository
      And DB 無任何紀錄
      When 呼叫 load_token_records(days=30)
      Then 回傳空列表

  Rule: UsageRepositoryProtocol 介面

    Scenario: UsageRepository 符合 Protocol
      Given 一個 UsageRepository 實例
      Then isinstance 檢查 UsageRepositoryProtocol 為 True

  Rule: record_audio 自動持久化

    Scenario: 有 repository 時自動寫入 DB
      Given 一個注入 mock repository 的 ExtendedUsageMonitor
      When 呼叫 record_audio 帶入 duration_sec 20.0 和 direction "output" 和 model "gemini-2.0-flash"
      Then audio_records 新增一筆紀錄
      And repository 的 save_audio_record 被呼叫一次

    Scenario: 無 repository 時僅存記憶體
      Given 一個無 repository 的 ExtendedUsageMonitor
      When 呼叫 record_audio 帶入 duration_sec 20.0 和 direction "output" 和 model "gemini-2.0-flash"
      Then audio_records 新增一筆紀錄

  Rule: record_and_persist 持久化 token 紀錄

    Scenario: 有 repository 時 token 紀錄寫入 DB
      Given 一個注入 mock repository 的 ExtendedUsageMonitor
      When 呼叫 record_and_persist 傳入含 80 input_tokens 和 40 output_tokens 的 usage
      Then records 新增一筆 UsageRecord
      And repository 的 save_token_record 被呼叫一次

    Scenario: 無 repository 時等同 record
      Given 一個無 repository 的 ExtendedUsageMonitor
      When 呼叫 record_and_persist 傳入含 80 input_tokens 和 40 output_tokens 的 usage
      Then records 新增一筆 UsageRecord

  Rule: App 啟動載入歷史

    Scenario: 啟動時載入歷史到 monitor
      Given 一個注入 mock repository 的 ExtendedUsageMonitor
      And repository 回傳 2 筆 token 歷史和 3 筆 audio 歷史
      When 呼叫 load_history()
      Then records 有 2 筆紀錄
      And audio_records 有 3 筆紀錄

    Scenario: 啟動時 DB 無紀錄
      Given 一個注入 mock repository 的 ExtendedUsageMonitor
      And repository 回傳空歷史
      When 呼叫 load_history()
      Then records 為空列表
      And audio_records 為空列表
