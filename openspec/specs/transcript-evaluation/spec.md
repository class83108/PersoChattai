## ADDED Requirements

### Requirement: 雙層評估 Pipeline
系統 SHALL 實作 `AssessmentService.evaluate()` 方法，執行 NLP → Claude → 後處理三階段 pipeline。

#### Scenario: 完整評估流程
- **WHEN** 對話結束且有有效 transcript
- **THEN** 系統 SHALL 依序執行：
  1. NLP Pipeline 計算量化指標
  2. Claude Agent（transcript_evaluator skill）質性分析
  3. 儲存評估結果至 assessments 表
  4. 更新 user_vocabulary 表
  5. 檢查是否需要產生 level_snapshot

#### Scenario: transcript 為空
- **WHEN** 對話結束但 transcript 為空（使用者立即取消）
- **THEN** 系統 SHALL 跳過評估，不建立 assessment 記錄

### Requirement: Claude Agent 質性分析
系統 SHALL 透過 BYOA Agent 的 `transcript_evaluator` skill，將 transcript + NLP metrics 送入 Claude 進行質性分析。

#### Scenario: 質性分析產出
- **WHEN** 將 transcript 和 NLP metrics 送入 Claude Agent
- **THEN** 系統 SHALL 收到包含以下欄位的結構化 JSON：
  - `cefr_level`: str（A1-C2）
  - `lexical_assessment`: str（詞彙評估描述）
  - `fluency_assessment`: str（流暢度評估描述）
  - `grammar_assessment`: str（語法評估描述）
  - `suggestions`: list[str]（改善建議）
  - `new_words`: list[str]（本次新出現的有意義詞彙）

#### Scenario: Claude API 失敗
- **WHEN** Claude Agent 呼叫失敗
- **THEN** 系統 SHALL 記錄 error log
- **AND** 評估 SHALL 僅保留 NLP 量化指標（cefr_level 為 null）
- **AND** 不影響對話狀態（仍為 completed）

### Requirement: 評估結果儲存
系統 SHALL 將每次評估結果寫入 `assessments` 表，包含量化指標和質性分析。

#### Scenario: 儲存完整評估
- **WHEN** 雙層評估完成
- **THEN** 系統 SHALL 建立 assessment 記錄，包含：
  - 所有 NLP 量化指標欄位
  - Claude 質性分析欄位
  - `conversation_id` 和 `user_id` 外鍵

#### Scenario: 儲存僅含量化指標的評估
- **WHEN** Claude 分析失敗但 NLP 指標計算成功
- **THEN** 系統 SHALL 建立 assessment 記錄，質性分析欄位為 null

### Requirement: 使用者詞彙更新
系統 SHALL 根據 Claude 評估結果中的 `new_words` 更新 `user_vocabulary` 表。

#### Scenario: 新增詞彙
- **WHEN** Claude 評估結果包含 new_words ["pragmatic", "nuanced"]
- **AND** 使用者詞彙庫中沒有這些詞
- **THEN** 系統 SHALL 在 user_vocabulary 中新增兩筆記錄
- **AND** `occurrence_count` SHALL 為 1

#### Scenario: 已知詞彙累加
- **WHEN** Claude 評估結果包含 new_words 中有使用者已知詞彙
- **THEN** 系統 SHALL 累加該詞的 `occurrence_count`
- **AND** 不更新 `first_seen_at`

### Requirement: Level Snapshot 聚合
系統 SHALL 在使用者累積每 5 次評估後自動產生 level_snapshot。

#### Scenario: 觸發 snapshot
- **WHEN** 使用者完成第 5、10、15... 次評估
- **THEN** 系統 SHALL 產生 level_snapshot，聚合最近 5 次評估的指標平均值
- **AND** 更新 `users.current_level`

#### Scenario: 未達觸發門檻
- **WHEN** 使用者完成的評估次數不是 5 的倍數
- **THEN** 系統 SHALL 不產生 snapshot

### Requirement: Assessment agent 透過 tool calling 查詢使用者歷史
Assessment agent SHALL 配備 `get_user_history` tool，使 `transcript_evaluator` skill 能在評估過程中查詢使用者歷史能力資料，而非由 service 層預先組合 prompt。

#### Scenario: Agent 評估時查詢歷史
- **WHEN** AssessmentService 呼叫 agent_run 請求評估 transcript
- **THEN** Agent 透過 `get_user_history` tool 取得使用者歷史，作為評估參考

#### Scenario: 新使用者無歷史仍可評估
- **WHEN** Agent 查詢歷史得到空結果
- **THEN** Agent 仍能完成評估，以 B1-B2 作為初始參考等級
