## Why

三大 Service（Content、Conversation、Assessment）的核心邏輯已實作並測試通過，但 BYOA Agent 目前無法透過 tool calling 存取 service 層資料。Skills 定義中引用的 `create_card`、`query_cards`、`get_user_history` tools 尚未註冊，導致 Agent 無法完成端到端的自動化流程（素材摘要→卡片建立、情境設計→歷史查詢、評估→詞彙追蹤）。這是 backend 整合的最後一塊拼圖。

## What Changes

- 實作三個 BYOA Tools（`query_cards`、`create_card`、`get_user_history`），handler 委派至對應 Service/Repository
- 建立 tool factory 函式，接收 repository/service 實例並回傳已註冊的 `ToolRegistry`
- 更新 `agent_factory.py`，將 `ToolRegistry` 傳入各 Agent 建構
- 實作 `agent_run` wrapper（收集 `stream_message` 結果並解析 JSON 回傳），讓 service 層統一呼叫
- 評估完成後自動更新 `user_vocabulary`（根據 Claude 輸出的 `new_words`）
- 每 5 次對話自動產生 `level_snapshot` 聚合

## Capabilities

### New Capabilities
- `byoa-tools`: 三個 BYOA tool 的定義、handler 實作、ToolRegistry 組裝
- `agent-run-wrapper`: Agent stream_message → 同步結果的 wrapper，供 service 層呼叫
- `post-assessment-pipeline`: 評估後自動化流程（vocabulary 更新 + snapshot 聚合）

### Modified Capabilities
- `content-summarizer`: 需整合 `create_card` tool，讓 Agent 能直接建立卡片
- `transcript-evaluation`: 需整合 `get_user_history` tool + 評估後觸發 vocabulary/snapshot 更新

## Impact

- **Code**: `agent_factory.py`（tool registry 組裝）、`content/service.py`、`assessment/service.py`、`conversation/manager.py`（改用 agent_run wrapper）
- **新增檔案**: `tools.py`（tool handlers + factory）、`agent_run.py`（wrapper）
- **Dependencies**: 無新增外部依賴，僅整合既有 BYOA Core API
- **API**: 無 REST API 變更，影響範圍限於 service 內部
