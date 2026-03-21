## Why

系統有完整的 Service 層、Router、Repository 但無法實際啟動——缺少 uvicorn 入口點、FastRTC 未掛載至 app、lifespan 未初始化 ConversationManager 和 ContentScheduler。此外 conversation router 缺少 cancel endpoint，timeout/silence 偵測未排程。這些都是讓系統從「有程式碼」變成「能運行」的必要整合。

## What Changes

- 新增 `__main__.py` 入口點，支援 `python -m persochattai` 啟動 uvicorn
- 擴充 `app.py` lifespan：初始化 ConversationManager、ContentScheduler、掛載 FastRTC stream
- 補齊 conversation router 的 `POST /{id}/cancel` endpoint
- 在 ConversationManager.start_conversation 中排程 timeout task（15 分鐘上限 + 13 分鐘警告）
- 在 ConversationManager.start_conversation 中啟動 silence monitor（2 分鐘靜默自動結束）

## Capabilities

### New Capabilities
- `app-bootstrap`: App 啟動流程——入口點、lifespan 整合、服務初始化順序

### Modified Capabilities
- `conversation-lifecycle`: 新增 cancel endpoint、timeout 排程、silence monitor 接線
- `conversation-api`: 補齊 cancel endpoint route

## Impact

- **修改檔案**: `app.py`（lifespan 擴充）、`conversation/router.py`（新增 cancel）、`conversation/manager.py`（timeout 排程）
- **新增檔案**: `__main__.py`
- **依賴**: 無新外部依賴（uvicorn 已在 dependencies）
- **下游**: 前端開發依賴此 change 完成後才能連接 API
