## Context

Foundation 已完成：FastAPI app factory、三個 service router 骨架、BYOA agent factory（含 `scenario_designer` skill）、DB schema（含 `conversations` 表）。

現在要實作 Conversation Service 的核心——Gemini Live API 語音對話。技術棧：
- **FastRTC** 的 `AsyncStreamHandler` 封裝 WebRTC 音訊流
- **google-genai** 的 `aio.live.connect()` 建立 Gemini Live session，內建 `input_transcription` + `output_transcription`
- **BYOA** 的 `scenario_designer` skill 生成 system instruction

## Goals / Non-Goals

**Goals:**
- 使用者可透過 WebRTC 與 Gemini 進行即時語音 Role Play 對話
- 對話期間自動收集雙向 transcript（使用者說的 + Gemini 回的）
- 對話結束後 transcript 持久化至 DB
- 完整的對話狀態機（preparing → active → completed / failed / cancelled）
- 對話 reset 機制（手動結束、時間上限、靜默超時）

**Non-Goals:**
- 前端 UI（本次只做 API + WebRTC signaling，前端另開 change）
- Assessment pipeline（下游 service，本次只觸發通知）
- 自由對話模式（P1，MVP 先做 Role Play）
- 發音評估（P1+）
- 多人同時語音（concurrency_limit=1 per session）

## Decisions

### 1. GeminiHandler 架構

**選擇：** 單一 `GeminiHandler(AsyncStreamHandler)` 負責音訊串流 + transcript 收集，conversation 生命週期由 `ConversationManager` 管理。

**理由：** FastRTC 要求每個 WebRTC 連線有獨立的 handler（透過 `copy()`），handler 只管音訊流，業務邏輯（狀態機、DB 寫入、timeout）交給 manager，職責清晰。

**替代方案：** 把所有邏輯放在 handler 裡 → cyclomatic complexity 過高、難測試。

### 2. Transcript 收集策略

**選擇：** 即時收集 transcript 事件至記憶體 list，對話結束時一次寫入 DB。

**理由：** Gemini Live API 的 `input_transcription` 和 `output_transcription` 是非同步事件，用 `finished: bool` 標記完成。收集到記憶體延遲最低，對話結束再批次寫入避免頻繁 DB I/O。單次對話 15 分鐘上限，transcript 資料量可控。

**替代方案：** 每句即時寫 DB → 不必要的 I/O，且 transcript 事件是增量的（partial text），需等 `finished=True` 才有完整句。

### 3. 對話狀態管理

**選擇：** `ConversationManager` 持有 in-memory 狀態（dict[conversation_id → state]），狀態變更同步寫 DB `conversations.status`。

**理由：** 同時活躍的對話數量極少（~10 使用者），in-memory 足夠。DB 寫入確保重啟後可恢復已完成的對話記錄。

**狀態轉換：**
```
preparing → connecting → active → assessing → completed
                │            │
                └→ failed    ├→ cancelled（使用者取消）
                             └→ failed（斷線）
```

### 4. Timeout 實作

**選擇：** `asyncio.Task` + `asyncio.Event`，不用 APScheduler。

**理由：** 對話 timeout 是 per-session 短期計時器（15 分鐘上限、2 分鐘靜默），跟 task 同生命週期用 asyncio 原生機制最直接。APScheduler 適合跨 session 的定期排程（如爬蟲）。

- 15 分鐘上限：`asyncio.sleep(13*60)` 發警告，`asyncio.sleep(2*60)` 後結束
- 靜默偵測：每次收到 `receive()` 重置計時器，2 分鐘無輸入觸發結束

### 5. FastRTC Mount 路徑

**選擇：** `Stream.mount(app, path="/api/conversation/rtc")`

**理由：** 與 conversation router 路徑一致（`/api/conversation/`），FastRTC 自動生成 `/api/conversation/rtc/webrtc/offer` endpoint。

### 6. Scenario 生成時機

**選擇：** 建立對話時同步呼叫 `scenario_designer`（BYOA agent），拿到 system instruction 後才建立 Gemini session。

**理由：** system instruction 是 Gemini Live `connect()` 的必要參數，必須先準備好。Claude 回應通常 < 5 秒，使用者在 preparing 狀態下等待可接受。

## Risks / Trade-offs

**[Gemini Live API 斷線]** → GeminiHandler 的 receiver loop 加 try/except，斷線時設狀態為 failed，保留已收集的 transcript。提供 data channel 通知前端。

**[transcript 品質不穩定]** → Gemini 的 transcript 是 best-effort，可能有遺漏或不準確。MVP 階段接受此限制，transcript 品質直接影響 Assessment 準確度。未來可考慮對 transcript 做後處理校正。

**[WebRTC 連線失敗率]** → FastRTC 處理底層 ICE/STUN/TURN，VPS 環境需確保 UDP port 開放。如果 NAT 穿透失敗，使用者看到 failed 狀態 + 重試按鈕。

**[concurrency_limit]** → 設為 `None`（不限制），因為 `copy()` 建立獨立 handler，每個使用者有自己的 Gemini session。10 個使用者同時對話的機率低，且 Gemini API 側有自己的 rate limit。

## Open Questions

- Gemini Live API 的音訊格式（sample rate、encoding）與 FastRTC 預設值是否需要調整？需實測確認。
- `send_realtime_input()` 接收的 PCM 格式 `rate=16000`，但 FastRTC 的 `input_sample_rate` 預設 48000——需要在 handler 中做 resample。
