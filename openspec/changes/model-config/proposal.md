## Why

Claude 和 Gemini 的模型 ID 目前 hardcoded 在 `agent_factory.py`（預設 `claude-sonnet-4-20250514`）和 `gemini_handler.py`（`gemini-2.0-flash-exp`），使用者無法切換。新模型頻繁推出（Claude 4.6 系列、Gemini 2.5 Flash），管理員需要能從前端切換而不改 code。此外 `GEMINI_AUDIO_PRICING` 的每秒定價是 placeholder，需修正為 token-based 正確計算。

## What Changes

- `Settings` 新增 `claude_model` / `gemini_model` 欄位（有 default，可 env 覆蓋）
- `agent_factory.py` 改用 `settings.claude_model`
- `gemini_handler.py` 改用 `settings.gemini_model`
- 修正 `GEMINI_AUDIO_PRICING`：改為 token-based 定價（25 tokens/sec × USD/MTok）
- 新增可選模型清單 + 對應定價表（Claude + Gemini）
- 新增 `/api/settings` GET/PUT 端點，讓前端讀取/切換模型
- `ExtendedUsageMonitor` 的 `model` 欄位隨 settings 連動

## Capabilities

### New Capabilities
- `model-switching`: 可透過 API 讀取與切換 Claude / Gemini 模型，定價表隨模型連動

### Modified Capabilities
- `gemini-usage-tracking`: 修正音訊定價為 token-based 正確值

## Impact

- **Code**: `config.py`、`agent_factory.py`、`gemini_handler.py`、`usage/schemas.py`、`app.py`
- **API**: 新增 `/api/settings` 端點（GET 讀取、PUT 更新模型）
- **Dependencies**: 無新增外部依賴
