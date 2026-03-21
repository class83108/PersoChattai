## Context

三大 Service 已實作完成（173 tests passing），Agent factory 已定義三個 Skills 但未註冊任何 Tools。BYOA Core 的 Agent 只提供 `stream_message()` async iterator API，而 Service 層需要一個同步收集結果的呼叫方式。目前 Service 層的 `agent.run()` 呼叫尚未實際連接到 BYOA Core。

## Goals / Non-Goals

**Goals:**
- 三個 BYOA Tools 能透過 LLM tool calling 存取 Service 層資料
- Service 層能透過統一 wrapper 呼叫 Agent 並取得結構化結果
- 評估完成後自動更新 vocabulary + 條件式產生 snapshot

**Non-Goals:**
- 不改變 REST API 介面
- 不實作前端整合
- 不擴展 UsageMonitor（留待後續 change）
- 不新增 BYOA Core 的 Protocol 或修改 upstream

## Decisions

### 1. Tool handler 以 closure 包裝 repository 實例

```python
def build_tool_registry(
    card_repo: CardRepositoryProtocol,
    assessment_repo: AssessmentRepositoryProtocol,
    vocabulary_repo: VocabularyRepositoryProtocol,
    snapshot_repo: SnapshotRepositoryProtocol,
) -> ToolRegistry:
```

每個 tool handler 是一個 closure，capture 對應的 repository。這避免了 global state，且符合 BYOA Core 的 `register(name, description, parameters, handler)` API。

**替代方案：** 用 class-based handler → 增加不必要的層級，closure 更簡潔。

### 2. agent_run wrapper 收集 stream 並解析 JSON

```python
async def agent_run(agent: Agent, message: str) -> dict[str, Any]:
    chunks = []
    async for event in agent.stream_message(content=message):
        if isinstance(event, str):
            chunks.append(event)
    text = "".join(chunks)
    return _extract_json(text)
```

Wrapper 負責：收集 stream chunks → 組合文字 → 提取 JSON（支援 markdown code fence 包裝）。

**替代方案：** Monkey-patch Agent.run() → 破壞 upstream 封裝，不可取。

### 3. Tool registry 按 Agent 角色拆分

| Agent | Tools |
|-------|-------|
| content_agent | `create_card` |
| conversation_agent | `query_cards`, `get_user_history` |
| assessment_agent | `get_user_history` |

每個 Agent 只看到需要的 tools，避免不必要的 token 消耗和混淆。使用 `ToolRegistry.clone(exclude=[...])` 或建立多個 registry。

### 4. Post-assessment pipeline 放在 AssessmentService.evaluate() 內

評估完成後，在同一個 `evaluate()` 方法內：
1. 解析 Claude 回傳的 `new_words`
2. 呼叫 `vocabulary_repo.upsert_words()`
3. 查詢 `assessment_repo.count_by_user()` 判斷是否達到 5 的倍數
4. 若是，聚合最近 5 次評估產生 snapshot

這避免引入額外的 event bus 或 background task 機制。

**替代方案：** 用 event/signal pattern → 對目前規模來說 over-engineering。

### 5. Tool parameters 使用 JSON Schema dict

BYOA Core 的 `ToolRegistry.register()` 接受 `parameters: dict[str, Any]`（JSON Schema 格式）。直接定義 dict 而非從 Pydantic model 轉換，減少間接層。

## Risks / Trade-offs

- **[stream_message API 可能回傳 AgentEvent 而非 str]** → wrapper 只收集 str chunks，忽略 AgentEvent（tool call events 由 Agent 內部處理）
- **[JSON 解析失敗]** → wrapper 回傳原始文字包在 `{"raw": text}` 中，service 層處理 fallback
- **[tool handler 中的 async 呼叫]** → BYOA Core 的 `execute()` 支援 async handler，已確認
- **[snapshot 聚合在 evaluate() 中同步執行]** → 若效能有問題，後續可改為 background task
