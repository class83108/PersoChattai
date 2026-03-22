## Why

Role Play 頁面（`/roleplay`）目前只是 placeholder。這是整個學習迴圈的核心 — 使用者透過即時語音與 AI 角色扮演練習英文。後端已有 Conversation Service API 和 FastRTC WebRTC stream，需要前端頁面串接並提供完整的對話體驗。

## What Changes

- 實作對話啟動流程：選擇素材來源 → 開始對話
- WebRTC 語音連線介面（FastRTC client 整合）
- 對話狀態指示器（preparing → connecting → active → assessing → completed）
- 對話進行中 UI：計時器、音量指示器、結束對話按鈕
- 對話歷史列表（過去的對話紀錄）
- 錯誤處理與重試

## Capabilities

### New Capabilities
- `conversation-ui`: 對話啟動流程、素材來源選擇、WebRTC 語音連線、狀態指示器
- `conversation-controls`: 對話中控制元件：計時器、音量指示、結束/取消按鈕
- `conversation-history`: 對話歷史列表，顯示過去的對話紀錄與狀態

### Modified Capabilities
（無既有 capability 需要修改）

## Impact

- **修改檔案**: `templates/pages/roleplay.html`（從 placeholder 改為完整頁面）
- **新增檔案**: `templates/partials/conversation_*.html` 系列 partial templates
- **新增檔案**: `static/js/roleplay.js`（WebRTC client、狀態管理、計時器）
- **修改路由**: frontend router 新增 conversation 相關 partial 端點
- **依賴**: `/api/conversation/*` API + FastRTC WebRTC stream（`/api/conversation/rtc`）
