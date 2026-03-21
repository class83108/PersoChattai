## 1. DB Migration + Schema

- [x] 1.1 建立 `migrations/003_model_config.sql`：`model_config` table（provider, model_id, display_name, is_active, pricing JSONB, timestamps）
- [x] 1.2 新增 `usage/schemas.py`：`ModelConfig` dataclass（對應 DB table）、`ModelConfigRepositoryProtocol`
- [x] 1.3 修改 `usage/schemas.py`：移除舊的 `GEMINI_AUDIO_PRICING` / `DEFAULT_GEMINI_AUDIO_PRICING` 常數

## 2. ModelConfig Repository

- [x] 2.1 建立 `usage/model_config_repository.py`：`ModelConfigRepository`（asyncpg）實作 Protocol — list_models, get_active_model, set_active_model, create_model, update_model, delete_model
- [x] 2.2 Seed 邏輯：啟動時若 table 為空，自動 seed 預設模型（Claude sonnet/opus/haiku + Gemini 2.0-flash/2.5-flash）

## 3. Settings + 整合

- [x] 3.1 修改 `config.py`：`Settings` 加入 `claude_model` / `gemini_model` 欄位（env 覆蓋，作為 DB 為空時的 fallback）
- [x] 3.2 修改 `agent_factory.py`：`init_usage_monitor()` 接受 `model_config_repo` 參數
- [x] 3.3 修改 `stream.py`：`GeminiHandler` 建構時傳入 model 參數

## 4. Gemini 定價修正

- [x] 4.1 修改 `usage/monitor.py`：`_gemini_audio_cost()` 改用 token-based 計算，定價從 DB model_config 取得

## 5. API 端點

- [x] 5.1 新增 `/api/models` GET 端點：列出所有模型（含定價）
- [x] 5.2 新增 `/api/models` POST 端點：新增模型（驗證 provider、必要定價欄位）
- [x] 5.3 新增 `/api/models/{model_id}` PUT 端點：更新模型定價或 display_name
- [x] 5.4 新增 `/api/models/{model_id}` DELETE 端點：刪除模型（不可刪除 active model）
- [x] 5.5 新增 `/api/settings` GET 端點：回傳當前 active model + 可選清單
- [x] 5.6 新增 `/api/settings` PUT 端點：切換 active model（驗證 model_id 在 DB 中）

## 6. App 啟動整合

- [x] 6.1 修改 `app.py`：lifespan 中初始化 ModelConfigRepository、執行 seed、注入 model_config_repo
