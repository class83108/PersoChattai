## ADDED Requirements

### Requirement: api_usage 資料表結構

系統 SHALL 提供 `api_usage` PostgreSQL 表，以 `usage_type` 欄位區分 token 和 audio 紀錄。

#### Scenario: 存入 token 類型紀錄
- **WHEN** 寫入一筆 `usage_type="token"` 的紀錄
- **THEN** `input_tokens`、`output_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens` 欄位有值
- **THEN** `audio_duration_sec` 和 `direction` 為 null

#### Scenario: 存入 audio 類型紀錄
- **WHEN** 寫入一筆 `usage_type="audio"` 的紀錄
- **THEN** `audio_duration_sec`、`direction`、`model` 欄位有值
- **THEN** token 相關欄位為 null

### Requirement: UsageRepository 寫入紀錄

`UsageRepository` SHALL 提供 `save_token_record(record, model)` 和 `save_audio_record(record)` async 方法，將紀錄寫入 `api_usage` 表。

#### Scenario: 寫入 token 紀錄
- **WHEN** 呼叫 `save_token_record(usage_record, model="claude-sonnet-4-20250514")`
- **THEN** `api_usage` 表新增一筆 `usage_type="token"` 的紀錄，包含正確的 token 數和 model

#### Scenario: 寫入 audio 紀錄
- **WHEN** 呼叫 `save_audio_record(audio_record)`
- **THEN** `api_usage` 表新增一筆 `usage_type="audio"` 的紀錄，包含正確的秒數和方向

### Requirement: UsageRepository 載入歷史紀錄

`UsageRepository` SHALL 提供 `load_token_records(days)` 和 `load_audio_records(days)` async 方法，從 DB 載入指定天數內的歷史紀錄。

#### Scenario: 載入最近 30 天的 token 紀錄
- **WHEN** 呼叫 `load_token_records(days=30)`
- **THEN** 回傳最近 30 天內的 `UsageRecord` 列表，按 `created_at` 排序

#### Scenario: 載入最近 30 天的 audio 紀錄
- **WHEN** 呼叫 `load_audio_records(days=30)`
- **THEN** 回傳最近 30 天內的 `GeminiAudioRecord` 列表，按 `created_at` 排序

#### Scenario: 無歷史紀錄時回傳空列表
- **WHEN** DB 無任何紀錄時呼叫 `load_token_records()`
- **THEN** 回傳空列表

### Requirement: UsageRepositoryProtocol 介面定義

系統 SHALL 定義 `UsageRepositoryProtocol`（Protocol class），包含 `save_token_record`、`save_audio_record`、`load_token_records`、`load_audio_records` 方法簽名，供 `ExtendedUsageMonitor` 依賴注入。

#### Scenario: Repository 符合 Protocol
- **WHEN** `UsageRepository` 實作所有 Protocol 方法
- **THEN** `isinstance(repo, UsageRepositoryProtocol)` 為 True（runtime_checkable）

### Requirement: record_audio 自動持久化

`ExtendedUsageMonitor.record_audio()` SHALL 在記錄音訊後自動呼叫 repository 的 `save_audio_record()` 寫入 DB（若 repository 存在）。

#### Scenario: 有 repository 時自動寫入
- **WHEN** `ExtendedUsageMonitor` 初始化時注入 repository，呼叫 `record_audio()`
- **THEN** 紀錄同時存入記憶體和 DB

#### Scenario: 無 repository 時僅存記憶體
- **WHEN** `ExtendedUsageMonitor` 初始化時未注入 repository，呼叫 `record_audio()`
- **THEN** 紀錄只存入記憶體的 `audio_records`，不嘗試 DB 寫入

### Requirement: record_and_persist 持久化 token 紀錄

`ExtendedUsageMonitor` SHALL 提供 `record_and_persist(usage)` async 方法，先呼叫 `record(usage)` 再呼叫 repository 的 `save_token_record()` 寫入 DB。

#### Scenario: 有 repository 時 token 紀錄寫入 DB
- **WHEN** 呼叫 `record_and_persist(usage)`
- **THEN** `UsageRecord` 存入記憶體且寫入 DB

#### Scenario: 無 repository 時等同 record()
- **WHEN** 未注入 repository 時呼叫 `record_and_persist(usage)`
- **THEN** 行為等同 `record(usage)`，只存記憶體

### Requirement: App 啟動時載入歷史

App lifespan SHALL 在啟動時從 DB 載入歷史紀錄到 `ExtendedUsageMonitor`。

#### Scenario: 啟動載入歷史
- **WHEN** App 啟動且 DB 有歷史紀錄
- **THEN** `ExtendedUsageMonitor.records` 包含歷史 token 紀錄
- **THEN** `ExtendedUsageMonitor.audio_records` 包含歷史 audio 紀錄

#### Scenario: 啟動時 DB 無紀錄
- **WHEN** App 啟動且 DB 無歷史紀錄
- **THEN** `records` 和 `audio_records` 均為空列表
