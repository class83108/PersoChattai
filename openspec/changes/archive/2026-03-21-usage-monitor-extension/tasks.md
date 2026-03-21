## 1. 資料結構與定價模型

- [x] 1.1 建立 `usage/schemas.py`：`GeminiAudioRecord` dataclass + `GEMINI_AUDIO_PRICING` 定價表 + `UsageRepositoryProtocol`
- [x] 1.2 建立 `usage/monitor.py`：`ExtendedUsageMonitor` 繼承 `UsageMonitor`，實作 `record_audio()`、`record_and_persist()`、覆寫 `get_summary()`

## 2. DB 持久化

- [x] 2.1 建立 `api_usage` 表 migration SQL
- [x] 2.2 建立 `usage/repository.py`：`UsageRepository`（asyncpg），實作 `save_token_record`、`save_audio_record`、`load_token_records`、`load_audio_records`

## 3. 整合

- [x] 3.1 更新 `agent_factory.py`：`_get_usage_monitor()` 改用 `ExtendedUsageMonitor`，注入 repository
- [x] 3.2 更新 `app.py`：lifespan 啟動時載入歷史紀錄到 `ExtendedUsageMonitor`
- [x] 3.3 確認 `/api/usage` 端點回傳擴展後的 summary（含 `gemini_audio` 區塊）
