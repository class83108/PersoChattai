## ADDED Requirements

### Requirement: 摘要 pipeline
系統 SHALL 提供 ContentService，將原始文字內容透過 Claude Agent（content_summarizer skill）轉換為標準化卡片。

#### Scenario: Podcast 文章摘要
- **WHEN** 輸入 source_type 為 podcast 的 RawArticle（含 title、content、url）
- **THEN** 系統呼叫 Claude Agent 摘要，產出一或多張卡片，每張卡片包含 title、summary（3-5 句）、keywords（含 word、definition、example）、difficulty_level（CEFR）、tags

#### Scenario: PDF 內容摘要
- **WHEN** 輸入 source_type 為 user_pdf 的文字內容
- **THEN** 系統呼叫 Claude Agent 摘要，產出一或多張卡片並儲存至 DB

#### Scenario: 自由主題展開
- **WHEN** 輸入 source_type 為 user_prompt 的主題描述
- **THEN** 系統呼叫 Claude Agent 展開主題為情境 prompt，產出一張卡片並儲存至 DB

### Requirement: 摘要結果儲存
摘要產出的卡片 SHALL 自動透過 CardRepository 儲存至 cards 表。

#### Scenario: 單篇素材產出多張卡片
- **WHEN** Claude Agent 判斷內容適合拆成多張卡片
- **THEN** 系統為每張卡片分別建立記錄，所有卡片共用相同的 source_url

#### Scenario: 摘要失敗
- **WHEN** Claude Agent 呼叫失敗或回傳非預期格式
- **THEN** 系統記錄 error log，回傳明確的錯誤訊息，不建立部分卡片

### Requirement: Content agent 透過 tool calling 建立卡片
Content agent SHALL 配備 `create_card` tool，使 `content_summarizer` skill 能在摘要過程中直接呼叫 tool 建立卡片，而非由 service 層解析 Agent 文字輸出後手動建立。

#### Scenario: Agent 摘要後呼叫 create_card
- **WHEN** ContentService 呼叫 agent_run 請求摘要 podcast 文章
- **THEN** Agent 透過 `create_card` tool 直接建立卡片，回傳包含已建立卡片 id 的結果

#### Scenario: 一篇文章拆成多張卡片
- **WHEN** Agent 判斷內容應拆成多張卡片
- **THEN** Agent 多次呼叫 `create_card` tool，每次建立一張卡片
