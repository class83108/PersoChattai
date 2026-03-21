## MODIFIED Requirements

### Requirement: Assessment agent 透過 tool calling 查詢使用者歷史
Assessment agent SHALL 配備 `get_user_history` tool，使 `transcript_evaluator` skill 能在評估過程中查詢使用者歷史能力資料，而非由 service 層預先組合 prompt。

#### Scenario: Agent 評估時查詢歷史
- **WHEN** AssessmentService 呼叫 agent_run 請求評估 transcript
- **THEN** Agent 透過 `get_user_history` tool 取得使用者歷史，作為評估參考

#### Scenario: 新使用者無歷史仍可評估
- **WHEN** Agent 查詢歷史得到空結果
- **THEN** Agent 仍能完成評估，以 B1-B2 作為初始參考等級
