## Context

系統後端已有完整的 Service 層（Content / Conversation / Assessment）、Router、Repository，但缺少啟動整合：
- `app.py` 的 lifespan 只初始化了 DB pool 和 UsageMonitor，未初始化 ConversationManager、ContentScheduler
- `conversation/stream.py` 定義了 `mount_conversation_stream` 但從未被呼叫
- 無 `__main__.py`，無法 `python -m persochattai` 啟動
- conversation router 缺少 cancel endpoint
- ConversationManager 有 timeout 方法但從未排程

## Goals / Non-Goals

**Goals:**
- 讓 `python -m persochattai` 或 `uvicorn persochattai.app:create_app --factory` 可啟動完整系統
- lifespan 正確初始化所有服務並在 shutdown 時清理
- FastRTC WebRTC stream 掛載至 `/api/conversation/rtc`
- conversation cancel endpoint 可用
- 對話開始後自動排程 timeout（15 分鐘）和 silence monitor（2 分鐘）

**Non-Goals:**
- 前端 UI（下一個 change）
- 生產部署配置（Docker / systemd / nginx）
- Scraper job 的實際爬蟲邏輯填充（只確保 scheduler 在 lifespan 中啟動/關閉）

## Decisions

### 1. 入口點使用 `__main__.py`

支援 `python -m persochattai` 啟動，內部呼叫 uvicorn.run。

**替代方案**: 獨立 `main.py` 在專案根目錄 — 不符合 Python package 慣例。

### 2. Lifespan 初始化順序

```
startup:
  1. init DB pool
  2. seed model config defaults
  3. init UsageMonitor (load history)
  4. init ConversationManager (需要 repository + scenario_designer + gemini_client)
  5. mount FastRTC stream
  6. start ContentScheduler
  7. store all services in app.state

shutdown:
  6. shutdown ContentScheduler
  1. close DB pool
```

ConversationManager 依賴 DB pool（透過 ConversationRepository），所以必須在 pool 之後初始化。
ContentScheduler 最後啟動、最先關閉，確保不會在 pool 關閉後還執行 job。

**替代方案**: 用 Dependency Injection 容器 — 過度工程化，app.state 已足夠。

### 3. Timeout 排程用 asyncio.Task

在 `start_conversation` 成功進入 ACTIVE 狀態後建立 asyncio.Task：
- 13 分鐘後發 warning notification
- 15 分鐘後自動結束

已有 `_timeout_tasks` dict 和 `_on_time_limit_warning` / `_on_time_limit_reached` 方法，只需在 start 時排程。

**替代方案**: APScheduler one-off job — 增加對 scheduler 的耦合，asyncio.Task 更輕量。

### 4. Silence Monitor 用 timer reset 模式

`on_audio_received` 已在更新 `_silence_timers`。新增一個 periodic check task（每 10 秒檢查一次），若 last audio timestamp 距現在 > 120 秒則觸發 `handle_silence_timeout`。

**替代方案**: 每次收到 audio 時 cancel + re-create task — 高頻 cancel/create 不必要。

### 5. FastRTC 掛載時機

在 lifespan 中建立 stream 並 mount，而非在 `create_app` 中。因為 GeminiHandler 需要 gemini_api_key，這在 settings 中，settings 在 lifespan 才完全就緒。

## Risks / Trade-offs

- **[Risk] ConversationManager 的 `_conversations` 是 in-memory dict** → 重啟後遺失進行中對話。Mitigation: MVP 可接受，未來可改為從 DB 恢復 active conversations。
- **[Risk] FastRTC stream mount 在 lifespan 中可能與 FastAPI 的 route 註冊時機衝突** → Mitigation: 確認 `stream.mount()` 在 yield 前呼叫即可，FastAPI 在 startup 完成後才接受請求。
- **[Risk] silence monitor 的 periodic check 有最多 10 秒誤差** → 可接受，不需精確到秒。
