Feature: Agent Run Wrapper
  作為 Service 層
  我想要 透過 agent_run wrapper 呼叫 BYOA Agent 並取得結構化結果
  以便 統一處理 Agent 的 stream 輸出為可操作的 dict

  Rule: 有效 JSON 回傳應解析為 dict

    Scenario: Agent 回傳有效 JSON
      Given 一個 Agent 會輸出有效 JSON 字串 '{"cefr_level": "B1", "score": 72}'
      When 呼叫 agent_run 並傳入訊息 "evaluate this"
      Then 回傳結果為 dict 且包含 key "cefr_level" 值為 "B1"
      And 回傳結果包含 key "score" 值為 72

    Scenario: Agent 回傳 markdown code fence 包裝的 JSON
      Given 一個 Agent 會輸出 code fence 包裝的 JSON
        """
        ```json
        {"title": "Business English", "difficulty": "B2"}
        ```
        """
      When 呼叫 agent_run 並傳入訊息 "summarize"
      Then 回傳結果為 dict 且包含 key "title" 值為 "Business English"

  Rule: 無法解析為 JSON 時應 fallback 為 raw 文字

    Scenario: Agent 回傳純文字
      Given 一個 Agent 會輸出純文字 "這是一段無法解析的回應"
      When 呼叫 agent_run 並傳入訊息 "hello"
      Then 回傳結果包含 key "raw" 值為 "這是一段無法解析的回應"

    Scenario: Agent 無任何輸出
      Given 一個 Agent 不會產生任何輸出
      When 呼叫 agent_run 並傳入訊息 "empty"
      Then 回傳結果的 "raw" 為空字串

  Rule: 只收集文字 chunks 忽略 AgentEvent

    Scenario: stream 混合 str 和 AgentEvent
      Given 一個 Agent 會輸出混合的 stream 包含 AgentEvent 和文字 '{"result": "ok"}'
      When 呼叫 agent_run 並傳入訊息 "mixed"
      Then 回傳結果為 dict 且包含 key "result" 值為 "ok"

  Rule: JSON 前後有多餘內容仍應正確解析

    Scenario: JSON 前後有多餘空白
      Given 一個 Agent 會輸出有效 JSON 字串 '  {"status": "done"}  '
      When 呼叫 agent_run 並傳入訊息 "check"
      Then 回傳結果為 dict 且包含 key "status" 值為 "done"
