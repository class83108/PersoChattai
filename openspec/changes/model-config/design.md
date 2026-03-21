## Context

目前模型 ID hardcoded 在兩處：
- `agent_factory.py`：`UsageMonitor(model='claude-sonnet-4-20250514')` — BYOA Core 預設值
- `gemini_handler.py`：`model='gemini-2.0-flash-exp'` — 建構參數預設值

`Settings` dataclass 只有 API key，沒有模型欄位。`GEMINI_AUDIO_PRICING` 的定價是 placeholder（$0.0001/sec），實際 Gemini 按 token 計費（25 tokens/sec × USD/MTok）。

系統是小圈子使用，API key 由 server 端管理。模型切換是管理員行為，不需要 per-user 設定。模型更新頻繁（幾個月就可能換），定價也會變動，需要能從前端管理而非改 code。

## Goals / Non-Goals

**Goals:**
- 管理員可透過 API 端點切換 Claude / Gemini 的 active model
- 管理員可透過 API 端點新增/修改/刪除可選模型與定價
- 模型切換後定價自動連動（UsageMonitor 的成本計算正確）
- 修正 Gemini 音訊定價為 token-based 正確值
- 模型配置持久化於 DB，重啟不遺失

**Non-Goals:**
- 不做 per-user / per-conversation 模型設定（全域共用）
- 不做模型 A/B testing
- 不修改 BYOA Core 的 `MODEL_PRICING`（upstream）
- 不做前端 UI（留給 PWA change）

## Decisions

### D1: Settings 加入 model 欄位 + env 覆蓋（啟動預設值）

`Settings` 新增 `claude_model` 和 `gemini_model` 欄位，作為啟動時的預設值：
- `claude_model`: `'claude-sonnet-4-20250514'`
- `gemini_model`: `'gemini-2.0-flash'`

可透過 `CLAUDE_MODEL` / `GEMINI_MODEL` 環境變數覆蓋。這些值只在 DB 無 active model 時使用（fallback）。

`Settings` 維持 `frozen=True`，不做 runtime mutation。

**理由**: 環境變數是既有模式（`DB_URL`、`ANTHROPIC_API_KEY` 都是），部署時可直接設。DB 為空時系統仍能啟動。

### D2: DB 持久化模型配置 + 定價表

新增 `model_config` DB table，存放可選模型和定價資訊：

```sql
CREATE TABLE model_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL,          -- 'claude' | 'gemini'
    model_id TEXT NOT NULL UNIQUE,   -- e.g. 'claude-sonnet-4-20250514'
    display_name TEXT NOT NULL,      -- e.g. 'Claude Sonnet 4'
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    pricing JSONB NOT NULL,          -- 定價欄位，格式依 provider 不同
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Claude pricing JSONB: `{"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30}`（USD per million tokens）
Gemini pricing JSONB: `{"text_input": 0.10, "audio_input": 0.70, "output": 0.40, "tokens_per_sec": 25}`

啟動時 seed 預設模型（如果 table 為空）：
- Claude: sonnet ($3/$15), opus ($5/$25), haiku ($1/$5)
- Gemini: 2.0-flash, 2.5-flash

每個 provider 只有一個 `is_active = TRUE` 的模型（DB constraint 或 application-level 保證）。

**理由**: 模型和定價存 DB，管理員從前端即可新增模型或更新定價，不需要改 code 重部署。JSONB 讓不同 provider 的定價結構可以不同。

**替代方案**:
- hardcoded Python dict — 每次加模型或改定價都要改 code、重部署，不適合頻繁變動。
- Settings runtime mutation — 重啟後遺失，不適合。

### D3: Admin API 端點

模型管理：
- `GET /api/models` — 列出所有模型（含定價）
- `POST /api/models` — 新增模型
- `PUT /api/models/{model_id}` — 更新模型定價或 display_name
- `DELETE /api/models/{model_id}` — 刪除模型（不可刪除 active model）

設定讀取/切換：
- `GET /api/settings` — 回傳當前 active model + 可選模型清單
- `PUT /api/settings` — 切換 active model（驗證 model_id 存在於 DB）

切換後影響：
- `agent_factory` 下次建立 Agent 時使用新 active model
- `ExtendedUsageMonitor.model` 更新（影響後續 token 定價計算）
- `gemini_handler` 下次建立 session 時使用新 active model
- 不影響進行中的對話

**理由**: RESTful CRUD 分離——`/api/models` 管理模型清單，`/api/settings` 管理 active 選擇。職責清楚。

### D4: ModelConfigRepository + Protocol

新增 `ModelConfigRepository`（asyncpg），實作 `ModelConfigRepositoryProtocol`：

```python
@runtime_checkable
class ModelConfigRepositoryProtocol(Protocol):
    async def list_models(self, *, provider: str | None = None) -> list[ModelConfig]: ...
    async def get_active_model(self, provider: str) -> ModelConfig | None: ...
    async def set_active_model(self, provider: str, model_id: str) -> None: ...
    async def create_model(self, model: ModelConfig) -> ModelConfig: ...
    async def update_model(self, model_id: str, updates: dict) -> ModelConfig: ...
    async def delete_model(self, model_id: str) -> None: ...
```

Monitor 計算成本時透過 repository 查詢當前模型的定價，或啟動時 cache 到 memory。

**理由**: 與 `UsageRepository` 同樣的 Protocol-first 模式，方便測試。

## Risks / Trade-offs

- **[進行中對話]** 切換模型不影響進行中的 Gemini session（已建立的 session 用原模型） → 可接受，下次對話生效。
- **[啟動 seed]** 第一次啟動時自動 seed 預設模型。若需要更新 seed 資料（新模型上市），需手動更新 seed 邏輯或透過 API 新增 → 可接受，API 就是為此設計。
- **[BYOA Core 定價衝突]** 我們的 Claude 定價表與 BYOA Core `MODEL_PRICING` 不同 → `ExtendedUsageMonitor` 覆寫 `get_summary()` 時用 DB 的定價。
- **[DB 查詢頻率]** 每次計算成本都查 DB 太慢 → 啟動時 load 到 memory cache，切換模型時更新 cache。
