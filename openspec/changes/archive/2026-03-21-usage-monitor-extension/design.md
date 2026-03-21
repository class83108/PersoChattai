## Context

BYOA Core 的 `UsageMonitor` 是一個 `@dataclass`，追蹤 Claude/OpenAI 的 token 使用量，資料存在記憶體中的 `records: list[UsageRecord]`，重啟即遺失。PersoChattai 額外使用 Gemini Live API 進行語音對話，其計費模式是按音訊秒數而非 token 數，目前完全沒有追蹤。

現狀：
- `agent_factory.py` 建立一個共用的 `UsageMonitor` 單例
- `app.py` 的 `/api/usage` 端點呼叫 `get_usage_monitor().get_summary()`
- `UsageMonitor.record()` 使用 `getattr(usage, 'input_tokens', 0)` 擷取 token 數
- `UsageMonitor.get_summary()` 回傳 `tokens`, `cache`, `cost_estimate_usd`, `recent_records`
- DB 已有 asyncpg connection pool（`db.py`），其他 repository 用同一個 pool

## Goals / Non-Goals

**Goals:**
- 追蹤 Gemini Live API 的音訊用量（秒數）和成本
- 將所有 API 使用紀錄持久化到 PostgreSQL，重啟不遺失
- 擴展 `get_summary()` 包含 Gemini 音訊成本，向下相容現有格式
- 遵循既有 repository pattern（asyncpg + pool injection）

**Non-Goals:**
- 不改寫 BYOA Core 的 `UsageMonitor` 原始碼
- 不追蹤 Gemini text API（目前只用 Live API 語音）
- 不實作即時 dashboard 或 WebSocket 推播
- 不做用量告警或限額機制

## Decisions

### D1: 繼承 UsageMonitor dataclass（路線 A）

`ExtendedUsageMonitor` 繼承 `UsageMonitor`，新增 Gemini 音訊紀錄欄位與方法。

**理由**: `UsageMonitor` 是 `@dataclass`，可正常繼承。BYOA Core 的 `Agent` 建構時接收 `usage_monitor` 參數，傳入子類別仍相容（duck typing）。繼承讓我們保留原有 token 追蹤邏輯，只擴展 Gemini 部分。

**替代方案**: 組合模式（內部持有一個 `UsageMonitor` 實例）——但需要 delegate 所有既有方法，增加無謂的 boilerplate。

### D2: Gemini 音訊紀錄用獨立 dataclass

新增 `GeminiAudioRecord` dataclass，欄位：`timestamp`, `audio_duration_sec`, `direction`（input/output）。不混入 `UsageRecord`，因為計費單位完全不同（秒 vs token）。

**理由**: 職責分離——token 紀錄和音訊紀錄的計算邏輯不同，混在一起會讓 `UsageRecord` 變得雜亂。

### D3: 持久化用 hook 模式（record 後自動寫 DB）

Override `record()` 方法：先呼叫 `super().record(usage)` 取得 `UsageRecord`，再非同步寫入 DB。但 `record()` 是同步方法，無法直接 await。

解法：`ExtendedUsageMonitor` 持有一個可選的 `UsageRepositoryProtocol` 參照。`record()` 仍同步執行（保持 BYOA Core 相容），另提供 `record_and_persist()` async 方法供需要持久化的場景使用。Gemini 音訊紀錄的 `record_audio()` 本身就是 async。

**替代方案**: 用 background task 或 event bus 非同步寫入——但增加複雜度，目前 QPS 極低（每次對話幾筆），直接 await 就夠。

### D4: 單一 `api_usage` 表存兩種紀錄

用 `usage_type` 欄位區分 `token` 和 `audio`。Token 紀錄填 token 欄位，audio 紀錄填 `audio_duration_sec` 欄位，其餘為 null。

```
api_usage (
    id            UUID PRIMARY KEY,
    usage_type    TEXT NOT NULL,        -- 'token' | 'audio'
    model         TEXT,
    input_tokens  INT,
    output_tokens INT,
    cache_creation_input_tokens INT,
    cache_read_input_tokens     INT,
    audio_duration_sec FLOAT,
    direction     TEXT,                 -- 'input' | 'output' (audio only)
    cost_usd      FLOAT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

**理由**: 查詢統一、migration 簡單。兩種紀錄量都不大（每天 <100 筆），不需要分表。

**替代方案**: 分兩張表（`token_usage` + `audio_usage`）——查詢需 UNION，增加 repository 複雜度，目前規模不值得。

### D5: App 啟動時載入歷史到記憶體

在 `_lifespan` 中呼叫 repository 載入歷史紀錄到 `ExtendedUsageMonitor`，保持 `get_summary()` 同步計算的特性。

**理由**: `get_summary()` 在 BYOA Core 中是同步方法，如果改為每次查 DB 就需要改寫介面。歷史資料量小（重啟頻率低，每天 <100 筆），全部載入記憶體沒有問題。

### D6: Gemini 定價模型

```python
GEMINI_AUDIO_PRICING: dict[str, dict[str, float]] = {
    'gemini-2.0-flash': {
        'input_per_second': 0.0001,   # 依實際定價調整
        'output_per_second': 0.0002,
    },
}
```

定價獨立於 BYOA Core 的 `MODEL_PRICING`，因為計費單位不同。

## Risks / Trade-offs

- **[BYOA Core 升級風險]** `UsageMonitor` 的 `record()` 簽名或 `UsageRecord` 結構變動會影響子類別 → 繼承已有 BYOA Core 版本 pin（pyproject.toml），升級時檢查 changelog 即可。
- **[記憶體載入]** 長期累積的紀錄會佔記憶體 → 載入時限制最近 N 天（例如 30 天），summary 只算載入的紀錄。需要全歷史用 DB 直接查。
- **[sync/async 混合]** `record()` 是同步但 DB 寫入是 async → 提供獨立的 `record_and_persist()` async 方法，呼叫端需注意使用正確的方法。
- **[Gemini 定價變動]** 定價可能隨 API 更新變動 → 抽成常數，修改一處即可。
