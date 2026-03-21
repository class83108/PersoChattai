## 1. agent_run wrapper

- [x] 1.1 Feature 覆蓋率分析 + .feature 檔（agent_run wrapper）
- [x] 1.2 實作 `agent_run()` async wrapper（收集 stream、解析 JSON、code fence 處理）
- [x] 1.3 測試 green + ruff + pyright

## 2. BYOA Tools 定義與 handler

- [x] 2.1 Feature 覆蓋率分析 + .feature 檔（byoa-tools）
- [x] 2.2 實作 `query_cards` tool handler（closure 包裝 CardRepository）
- [x] 2.3 實作 `create_card` tool handler（closure 包裝 CardRepository）
- [x] 2.4 實作 `get_user_history` tool handler（closure 包裝 AssessmentService）
- [x] 2.5 實作 `build_tool_registry()` factory（按 agent 角色組裝 registry）
- [x] 2.6 測試 green + ruff + pyright

## 3. Agent factory 整合

- [x] 3.1 覆蓋率分析（純組裝邏輯，不額外寫 .feature）
- [x] 3.2 更新 `create_content_agent` 傳入 content tool registry
- [x] 3.3 更新 `create_conversation_agent` 傳入 conversation tool registry
- [x] 3.4 更新 `create_assessment_agent` 傳入 assessment tool registry
- [x] 3.5 更新 service 層改用 `agent_run` wrapper 呼叫 Agent
- [x] 3.6 測試 green + ruff + pyright（189 passed）

## 4. Post-assessment pipeline

- [x] 4.1 確認既有實作已涵蓋（evaluate 中 vocabulary 更新 + snapshot 聚合）
- [x] 4.2 既有 transcript_evaluation.feature 已覆蓋所有場景
- [x] 4.3 測試 green

## 5. 驗收

- [x] 5.1 全部 pytest 通過（189 tests = 173 既有 + 16 新增）
- [x] 5.2 ruff check + ruff format + pyright 通過
- [ ] 5.3 Design review
