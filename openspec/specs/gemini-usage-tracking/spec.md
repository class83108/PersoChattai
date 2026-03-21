## ADDED Requirements

### Requirement: ExtendedUsageMonitor 繼承 UsageMonitor

`ExtendedUsageMonitor` SHALL 繼承 BYOA Core 的 `UsageMonitor` dataclass，保留所有原有 token 追蹤功能，並新增 Gemini 音訊紀錄欄位 `audio_records: list[GeminiAudioRecord]`。

#### Scenario: 繼承後仍可追蹤 token 使用量
- **WHEN** 呼叫 `ExtendedUsageMonitor.record(usage)` 傳入含 `input_tokens` 和 `output_tokens` 的 usage 物件
- **THEN** 行為與原 `UsageMonitor.record()` 一致，建立 `UsageRecord` 並加入 `records`

#### Scenario: ExtendedUsageMonitor 可作為 UsageMonitor 傳入 Agent
- **WHEN** 將 `ExtendedUsageMonitor` 實例傳入需要 `UsageMonitor` 的地方
- **THEN** 通過 isinstance 檢查（`isinstance(monitor, UsageMonitor)` 為 True）

### Requirement: 記錄 Gemini 音訊用量

`ExtendedUsageMonitor` SHALL 提供 `record_audio(duration_sec, direction, model)` async 方法，記錄 Gemini Live API 的音訊用量。

#### Scenario: 記錄一筆 input 音訊
- **WHEN** 呼叫 `record_audio(duration_sec=30.5, direction="input", model="gemini-2.0-flash")`
- **THEN** 建立一筆 `GeminiAudioRecord`，`audio_duration_sec` 為 30.5、`direction` 為 "input"
- **THEN** 該紀錄加入 `audio_records` 列表

#### Scenario: 監控停用時不記錄音訊
- **WHEN** `enabled` 為 False 時呼叫 `record_audio()`
- **THEN** 不建立紀錄，回傳 None

### Requirement: GeminiAudioRecord 資料結構

`GeminiAudioRecord` SHALL 為 dataclass，包含 `timestamp`、`audio_duration_sec`（float）、`direction`（"input" | "output"）、`model`（str）欄位。

#### Scenario: 建立音訊紀錄
- **WHEN** 建立 `GeminiAudioRecord(timestamp=now, audio_duration_sec=10.0, direction="output", model="gemini-2.0-flash")`
- **THEN** 所有欄位可正常存取

#### Scenario: 序列化為 dict
- **WHEN** 呼叫 `GeminiAudioRecord.to_dict()`
- **THEN** 回傳包含 `timestamp`（ISO 格式）、`audio_duration_sec`、`direction`、`model` 的字典

### Requirement: Gemini 音訊定價計算

`ExtendedUsageMonitor` SHALL 根據 DB `model_config` 中的定價計算音訊成本。定價為 token-based：`duration_sec × tokens_per_sec × audio_input_price / 1_000_000`。

#### Scenario: 計算已知模型的音訊成本
- **WHEN** 有一筆 `gemini-2.0-flash` 的 input 音訊紀錄 30 秒
- **THEN** 成本為 `30 × 25 × 0.70 / 1_000_000`

#### Scenario: 未知模型使用 fallback 定價
- **WHEN** 模型名稱不在 DB model_config 中
- **THEN** 使用 FALLBACK_GEMINI_PRICING 計算成本並 log warning

### Requirement: 擴展 get_summary 包含 Gemini 成本

`ExtendedUsageMonitor.get_summary()` SHALL 在原有摘要基礎上新增 `gemini_audio` 區塊，包含音訊統計和成本。原有欄位格式不變。

#### Scenario: 有 token 和音訊紀錄時的 summary
- **WHEN** 有 2 筆 token 紀錄和 3 筆音訊紀錄時呼叫 `get_summary()`
- **THEN** 回傳包含原有 `tokens`、`cache`、`cost_estimate_usd` 區塊
- **THEN** 額外包含 `gemini_audio` 區塊，含 `total_duration_sec`、`total_requests`、`cost_usd`、`recent_records`

#### Scenario: 無音訊紀錄時 summary 仍包含 gemini_audio
- **WHEN** 只有 token 紀錄、無音訊紀錄時呼叫 `get_summary()`
- **THEN** `gemini_audio` 區塊的 `total_duration_sec` 為 0、`total_requests` 為 0、`cost_usd` 為 0

#### Scenario: 無任何紀錄時的 summary
- **WHEN** 無 token 也無音訊紀錄時呼叫 `get_summary()`
- **THEN** 回傳 `total_requests` 為 0 且包含 `message` 欄位
