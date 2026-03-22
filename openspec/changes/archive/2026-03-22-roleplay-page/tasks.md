## 1. User ID 管理

- [x] 1.1 在 `static/js/app.js` 加入 user_id 管理（localStorage UUID 生成/讀取）

## 2. Role Play 頁面結構

- [x] 2.1 重寫 `templates/pages/roleplay.html`：對話區域 + 歷史側欄（desktop）/ tab（mobile）
- [x] 2.2 素材來源選擇區：source_type select + source_ref input + 開始對話按鈕

## 3. 對話狀態 UI

- [x] 3.1 建立 `static/js/roleplay.js`：狀態機（idle → preparing → connecting → active → assessing → completed / failed）
- [x] 3.2 每個狀態對應的 UI 區塊（loading 動畫、文字提示、控制按鈕）
- [x] 3.3 麥克風權限檢查（getUserMedia），無權限時顯示提示

## 4. 對話控制元件

- [x] 4.1 計時器：active 狀態開始計時，結束時停止
- [x] 4.2 結束對話按鈕：呼叫 `/api/conversation/{id}/end`
- [x] 4.3 取消按鈕：呼叫 `/api/conversation/{id}/cancel`
- [x] 4.4 音量指示器：CSS 脈動動畫，基於 AudioContext analyser

## 5. WebRTC 連線

- [x] 5.1 整合 FastRTC WebRTC client（建立 RTCPeerConnection，連線 `/api/conversation/rtc`）
- [x] 5.2 連線失敗處理：顯示 failed 狀態 + 重試按鈕

## 6. 對話歷史

- [x] 6.1 建立 `templates/partials/conversation_history.html`（歷史列表 partial）
- [x] 6.2 建立 `templates/partials/conversation_history_item.html`（單筆紀錄）
- [x] 6.3 新增 `GET /roleplay/partials/history` 端點（代理 API + 渲染 partial）

## 7. Frontend Router 更新

- [x] 7.1 新增 roleplay 相關 partial 端點到 frontend router
