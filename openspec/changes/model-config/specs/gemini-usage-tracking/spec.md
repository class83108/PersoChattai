## MODIFIED Requirements

### Requirement: Gemini 音訊定價計算

`ExtendedUsageMonitor` SHALL 根據 DB `model_config` 中的定價計算音訊成本。定價為 token-based：`duration_sec × tokens_per_sec × audio_input_price / 1_000_000`。

#### Scenario: 計算已知模型的音訊成本
- **WHEN** 有一筆 `gemini-2.0-flash` 的 input 音訊紀錄 30 秒
- **THEN** 成本為 `30 × 25 × 0.70 / 1_000_000`

#### Scenario: 未知模型使用 fallback 定價
- **WHEN** 模型名稱不在 DB model_config 中
- **THEN** 使用 Settings fallback 定價計算成本並 log warning
