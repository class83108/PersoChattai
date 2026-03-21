## Why

BYOA Core 的 UsageMonitor 只追蹤 Claude/OpenAI 的 token 成本，且資料存在記憶體中（重啟即遺失）。PersoChattai 使用 Gemini Live API 進行語音對話（按音訊秒數計費），目前沒有追蹤 Gemini 用量和成本的機制，也沒有持久化任何 API 使用紀錄。

## What Changes

- 建立 `ExtendedUsageMonitor`（繼承 BYOA Core `UsageMonitor`）：
  - 新增 Gemini Live API 音訊計費追蹤（`audio_duration_sec`）
  - 新增 Gemini 定價模型
  - 擴展 `get_summary()` 包含 Gemini 音訊成本
- 新增 `api_usage` PostgreSQL 表 + repository adapter
- 新增 DB 持久化機制：每次 `record()` 自動寫入 DB，app 啟動時載入歷史紀錄
- 更新 `agent_factory.py` 使用 `ExtendedUsageMonitor`
- 更新 `/api/usage` 端點回傳擴展後的摘要

## Capabilities

### New Capabilities
- `gemini-usage-tracking`: Gemini Live API 音訊計費追蹤與定價計算
- `usage-persistence`: API 使用紀錄 PostgreSQL 持久化（寫入/載入/摘要）

### Modified Capabilities
（無既有 spec 的 requirement 變更，foundation spec 的 `/api/usage` 端點行為不變，只是回傳更多欄位）

## Impact

- **Code**: `agent_factory.py`（改用 ExtendedUsageMonitor）、`app.py`（lifespan 載入歷史）
- **新增檔案**: `usage/monitor.py`、`usage/repository.py`、`usage/schemas.py`
- **DB**: 新增 `api_usage` 表（migration）
- **API**: `/api/usage` 回傳格式擴展（向下相容，新增 `gemini_cost` 區塊）
- **Dependencies**: 無新增外部依賴
