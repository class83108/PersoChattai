Feature: Gemini Token-based 定價計算
  作為 PersoChattai 系統
  我想要 根據 DB 中的模型定價計算 Gemini 音訊成本
  以便 成本追蹤反映正確的 token-based 定價

  Rule: Token-based 成本計算

    Scenario: gemini-2.0-flash 音訊成本
      Given 一個 ExtendedUsageMonitor 且 DB 有 gemini-2.0-flash 定價（audio_input=0.70, tokens_per_sec=25）
      When 記錄一筆 30 秒 input 音訊（model "gemini-2.0-flash"）
      Then gemini_audio 成本為 0.000525

    Scenario: gemini-2.5-flash 音訊成本
      Given 一個 ExtendedUsageMonitor 且 DB 有 gemini-2.5-flash 定價（audio_input=1.00, tokens_per_sec=25）
      When 記錄一筆 30 秒 input 音訊（model "gemini-2.5-flash"）
      Then gemini_audio 成本為 0.00075

    Scenario: duration 為 0 時成本為 0
      Given 一個 ExtendedUsageMonitor 且 DB 有 gemini-2.0-flash 定價（audio_input=0.70, tokens_per_sec=25）
      When 記錄一筆 0 秒 input 音訊（model "gemini-2.0-flash"）
      Then gemini_audio 成本為 0.0

  Rule: Fallback 定價

    Scenario: 未知模型使用 fallback 定價並 log warning
      Given 一個 ExtendedUsageMonitor 且 DB 無 "unknown-gemini" 的定價
      When 記錄一筆 30 秒 input 音訊（model "unknown-gemini"）
      Then gemini_audio 成本使用 fallback 定價計算
      And 產生一筆 warning log

  Rule: get_summary 反映正確定價

    Scenario: get_summary 包含 token-based 成本
      Given 一個 ExtendedUsageMonitor 且 DB 有 gemini-2.0-flash 定價（audio_input=0.70, tokens_per_sec=25）
      When 記錄一筆 30 秒 input 音訊（model "gemini-2.0-flash"）
      Then get_summary() 的 gemini_audio.cost_usd 為 0.000525
