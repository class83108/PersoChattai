## Why

Conversation Service 是核心學習迴圈的中心環節——使用者透過語音 Role Play 練習英文。
Foundation 已建好骨架，現在需要實作完整的語音對話流程：素材選擇 → 情境生成 → Gemini Live 即時對話 → transcript 收集儲存，為下游的 Assessment Service 提供輸入。

## What Changes

- 實作 `GeminiHandler`（FastRTC `AsyncStreamHandler` 子類別），處理 Gemini Live API 雙向音訊串流 + transcript 收集
- 建立對話生命週期管理：preparing → connecting → active → assessing → completed（含 failed / cancelled）
- 整合 BYOA `scenario_designer` skill，根據素材 + 使用者能力生成 Gemini system instruction
- 實作對話 reset 邏輯：手動結束、15 分鐘上限、2 分鐘靜默超時、斷線處理
- 建立 conversation CRUD endpoints（建立對話、取得對話狀態、列出歷史）
- 實作 transcript 持久化至 PostgreSQL `conversations` 表
- FastRTC mount 至 FastAPI app，提供 WebRTC signaling

## Capabilities

### New Capabilities

- `gemini-realtime`: Gemini Live API 整合，GeminiHandler 音訊串流 + transcript 收集
- `conversation-lifecycle`: 對話狀態機、reset 觸發條件、timeout 管理
- `conversation-api`: REST endpoints — 建立對話、查詢狀態、列出歷史、結束對話

### Modified Capabilities

（無既有 spec 需修改）

## Impact

- **新增依賴**：`google-genai` + `fastrtc` 已在 pyproject.toml
- **修改檔案**：`src/persochattai/conversation/` 目錄下新增模組
- **修改 app.py**：FastRTC mount 至 FastAPI app
- **DB**：使用既有 `conversations` 表，無 schema 變更
- **依賴 foundation**：使用 `agent_factory.create_conversation_agent()`、`db.get_pool()`、`Settings`
