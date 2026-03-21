## ADDED Requirements

### Requirement: agent_run wrapper 收集 stream 並回傳結構化結果
系統 SHALL 提供 `agent_run(agent, message)` async 函式，收集 `agent.stream_message()` 的所有 str chunks，組合後嘗試解析為 JSON dict 回傳。

#### Scenario: Agent 回傳有效 JSON
- **WHEN** 呼叫 `agent_run` 且 Agent 輸出為合法 JSON 字串
- **THEN** 回傳解析後的 `dict[str, Any]`

#### Scenario: Agent 回傳 markdown code fence 包裝的 JSON
- **WHEN** Agent 輸出為 `` ```json\n{...}\n``` `` 格式
- **THEN** 自動剝離 code fence 後解析 JSON 並回傳 dict

#### Scenario: Agent 回傳非 JSON 文字
- **WHEN** Agent 輸出無法解析為 JSON
- **THEN** 回傳 `{"raw": "<原始文字>"}`

### Requirement: agent_run 只收集文字 chunks
`agent_run` SHALL 只收集 `str` 類型的 stream event，忽略 `AgentEvent` 類型（tool calling 由 Agent 內部處理）。

#### Scenario: stream 包含 AgentEvent
- **WHEN** Agent 在 stream 中產生 tool call event 和文字 chunks
- **THEN** wrapper 只收集文字 chunks，AgentEvent 被忽略
