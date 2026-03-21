## 1. 入口點與 Lifespan 基礎

- [x] 1.1 建立 `src/persochattai/__main__.py`，呼叫 uvicorn.run 啟動 create_app factory
- [x] 1.2 擴充 `app.py` lifespan：初始化 ConversationRepository、ScenarioDesigner callable、Gemini client
- [x] 1.3 擴充 `app.py` lifespan：建立 ConversationManager 並存入 app.state
- [x] 1.4 擴充 `app.py` lifespan：建立 AssessmentService 並注入 ConversationManager
- [x] 1.5 擴充 `app.py` lifespan：啟動 ContentScheduler 並在 shutdown 關閉

## 2. FastRTC 掛載

- [x] 2.1 在 lifespan 中呼叫 `mount_conversation_stream(app, model=settings.gemini_model)`
- [x] 2.2 確認 `/api/conversation/rtc` 路徑在 app 啟動後可用

## 3. Conversation Cancel Endpoint

- [x] 3.1 在 `conversation/router.py` 新增 `POST /{conversation_id}/cancel` endpoint
- [x] 3.2 處理 404（不存在）和 409（已結束）錯誤回應

## 4. Timeout 與 Silence Monitor

- [x] 4.1 在 ConversationManager 新增 `_schedule_timeout` 方法：13 分鐘 warning + 15 分鐘結束
- [x] 4.2 在 `start_conversation` 成功進入 ACTIVE 後呼叫 `_schedule_timeout`
- [x] 4.3 新增 `_start_silence_monitor` 方法：每 10 秒檢查 silence timer，> 120 秒觸發 handle_silence_timeout
- [x] 4.4 在 `start_conversation` 成功進入 ACTIVE 後呼叫 `_start_silence_monitor`
- [x] 4.5 在 `end_conversation`、`cancel_conversation`、timeout 結束時清理所有 tasks

## 5. Feature 覆蓋率分析與 Gherkin

- [x] 5.1 完成 feature 覆蓋率分析（6 類 checklist）並等待確認
- [x] 5.2 撰寫 `app_bootstrap.feature` — app 啟動、lifespan、health check
- [x] 5.3 撰寫或更新 `conversation_lifecycle.feature` — cancel、timeout、silence 相關 scenarios

## 6. TDD Red-Green

- [x] 6.1 撰寫 step definitions，執行 pytest 確認全紅
- [x] 6.2 實作 production code 讓測試全綠
- [x] 6.3 執行 `ruff check . --fix && ruff format . && pyright` 確認品質
