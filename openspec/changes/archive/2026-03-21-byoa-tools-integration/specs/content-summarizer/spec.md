## MODIFIED Requirements

### Requirement: Content agent 透過 tool calling 建立卡片
Content agent SHALL 配備 `create_card` tool，使 `content_summarizer` skill 能在摘要過程中直接呼叫 tool 建立卡片，而非由 service 層解析 Agent 文字輸出後手動建立。

#### Scenario: Agent 摘要後呼叫 create_card
- **WHEN** ContentService 呼叫 agent_run 請求摘要 podcast 文章
- **THEN** Agent 透過 `create_card` tool 直接建立卡片，回傳包含已建立卡片 id 的結果

#### Scenario: 一篇文章拆成多張卡片
- **WHEN** Agent 判斷內容應拆成多張卡片
- **THEN** Agent 多次呼叫 `create_card` tool，每次建立一張卡片
