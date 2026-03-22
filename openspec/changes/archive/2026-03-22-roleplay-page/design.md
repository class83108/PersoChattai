## Context

Role Play 頁面需要串接 Conversation Service API 和 FastRTC WebRTC stream。

後端已提供：
- `POST /api/conversation/start` — 建立對話（需要 user_id、source_type、source_ref）
- `GET /api/conversation/{id}` — 查詢對話狀態
- `POST /api/conversation/{id}/end` — 結束對話（觸發評估）
- `POST /api/conversation/{id}/cancel` — 取消對話
- `GET /api/conversation/history/{user_id}` — 對話歷史
- FastRTC WebRTC stream mount 在 `/api/conversation/rtc`

對話狀態：preparing → connecting → active → assessing → completed（+ failed / cancelled）

FastRTC 提供 WebRTC 連線，需要在前端用 JS 建立 RTCPeerConnection。

## Goals / Non-Goals

**Goals:**
- 素材來源選擇（從卡片或自由主題開始對話）
- WebRTC 語音連線（整合 FastRTC client）
- 狀態指示器（每個狀態有對應 UI）
- 對話計時器
- 結束/取消對話按鈕
- 對話歷史列表
- 連線失敗重試

**Non-Goals:**
- 不做 transcript 即時顯示（後端收集，事後顯示）
- 不做音量視覺化波形圖（只做簡單指示器）
- 不做多人對話
- 不做對話中切換素材

## Decisions

### 1. 狀態驅動 UI（State Machine in JS）

`roleplay.js` 維護一個簡單的狀態機，每個狀態對應不同的 UI 區塊（用 CSS class toggle 顯示/隱藏）。不用 HTMX 做狀態切換 — WebRTC 是持續連線，狀態變化由 JS 驅動。

替代方案：HTMX polling 查詢狀態 → 延遲太高，WebRTC 連線本身就是 JS 管理的。

### 2. FastRTC Client 整合

FastRTC 提供 WebRTC stream。前端需要：
1. 取得使用者麥克風權限（`getUserMedia`）
2. 建立 RTCPeerConnection
3. 連線到 `/api/conversation/rtc`（FastRTC 的 WebRTC signaling）

使用 FastRTC 提供的 JS client helper（如有），或手動建立 WebRTC 連線。

### 3. 對話歷史：HTMX partial

對話歷史列表使用 HTMX 動態載入（跟素材管理同模式），呼叫 `/api/conversation/history/{user_id}` 後渲染 partial。

### 4. 頁面結構：兩欄式

```
┌─────────────────────────────────────┐
│ Role Play                           │
├──────────────────┬──────────────────┤
│                  │                  │
│  對話區域         │  對話歷史         │
│  (狀態指示器)     │  (HTMX list)    │
│  (語音控制)       │                  │
│  (計時器)         │                  │
│                  │                  │
├──────────────────┴──────────────────┤
│  素材來源選擇（開始新對話）           │
└─────────────────────────────────────┘
```

Mobile：改為 tab 切換（對話 / 歷史），素材選擇在對話 tab 底部。

### 5. User ID

目前沒有登入系統。暫時使用 localStorage 存 UUID 作為 user_id，第一次訪問時生成。後續加入認證後替換。

## Risks / Trade-offs

- **WebRTC 瀏覽器相容性** → 現代瀏覽器都支援。Mitigation：啟動前檢查 `getUserMedia` 是否可用。
- **暫時 user_id** → 換瀏覽器/清 storage 會失去歷史。Mitigation：後續加認證時遷移。
- **FastRTC signaling 細節** → 需要了解 FastRTC 的 WebRTC offer/answer 流程。Mitigation：先實作 UI 框架，WebRTC 連線細節可後續調整。
