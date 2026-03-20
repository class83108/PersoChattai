## 1. Pydantic Models + DB Repository

- [ ] 1.1 建立 conversation/models.py — ConversationCreate, ConversationState, TranscriptEntry 等 Pydantic models
- [ ] 1.2 建立 conversation/repository.py — conversations 表 CRUD（create, update_status, save_transcript, get_by_id, list_by_user）

## 2. GeminiHandler（FastRTC + Gemini Live）

- [ ] 2.1 建立 conversation/gemini_handler.py — GeminiHandler(AsyncStreamHandler) 骨架（receive, emit, copy, start_up）
- [ ] 2.2 實作 Gemini Live session 建立（connect + config + system_instruction）
- [ ] 2.3 實作 receiver loop（從 Gemini 接收音訊 + transcript 事件）
- [ ] 2.4 實作 transcript 收集邏輯（input/output_transcription, finished 判斷）
- [ ] 2.5 實作斷線處理（receiver loop exception → 保留 transcript + 通知上層）

## 3. ConversationManager（狀態機 + Timeout）

- [ ] 3.1 建立 conversation/manager.py — ConversationManager 骨架（start, end, get_state）
- [ ] 3.2 實作狀態機轉換邏輯（preparing → connecting → active → assessing → completed / failed / cancelled）
- [ ] 3.3 實作 scenario_designer 整合（呼叫 BYOA agent 生成 system instruction）
- [ ] 3.4 實作 15 分鐘時間上限（13 分鐘警告 + 15 分鐘自動結束）
- [ ] 3.5 實作 2 分鐘靜默超時（receive 重置計時器）
- [ ] 3.6 實作對話結束流程（儲存 transcript 至 DB + 清理資源）

## 4. REST API Endpoints

- [ ] 4.1 實作 POST /api/conversation/start — 建立對話
- [ ] 4.2 實作 GET /api/conversation/{conversation_id} — 查詢對話狀態
- [ ] 4.3 實作 POST /api/conversation/{conversation_id}/end — 結束對話
- [ ] 4.4 實作 GET /api/conversation/history/{user_id} — 列出對話歷史

## 5. FastRTC 整合

- [ ] 5.1 建立 Stream mount 至 FastAPI app（/api/conversation/rtc）
- [ ] 5.2 整合 GeminiHandler + ConversationManager（handler 事件回呼 manager）

## 6. 驗證

- [ ] 6.1 撰寫 .feature 檔（conversation-api, conversation-lifecycle）
- [ ] 6.2 撰寫 pytest-bdd step definitions
- [ ] 6.3 確認 ruff check + ruff format + pyright 全部通過
