## ADDED Requirements

### Requirement: 評估完成後自動更新 user_vocabulary
`AssessmentService.evaluate()` SHALL 在 Claude 評估回傳 `new_words` 後，自動呼叫 `vocabulary_repo.upsert_words()` 寫入使用者詞彙表。

#### Scenario: 評估包含新詞彙
- **WHEN** Claude 評估結果包含 `new_words: ["eloquent", "persuasive"]`
- **THEN** 這兩個詞寫入 `user_vocabulary` 表，`occurrence_count` 遞增

#### Scenario: 評估無新詞彙
- **WHEN** Claude 評估結果的 `new_words` 為空列表
- **THEN** 不呼叫 `upsert_words()`，不產生 DB 寫入

#### Scenario: 詞彙已存在
- **WHEN** `new_words` 包含使用者已記錄過的詞彙
- **THEN** 該詞的 `occurrence_count` 遞增，`first_seen_at` 不變

### Requirement: 每 5 次對話自動產生 level_snapshot
`AssessmentService.evaluate()` SHALL 在每次評估後檢查使用者的總評估次數，當達到 5 的倍數時自動聚合最近 5 次評估產生 `level_snapshot`。

#### Scenario: 第 5 次評估觸發 snapshot
- **WHEN** 使用者完成第 5 次對話評估
- **THEN** 自動聚合最近 5 次評估，產生 snapshot 寫入 `user_level_snapshots` 表

#### Scenario: 第 3 次評估不觸發
- **WHEN** 使用者完成第 3 次對話評估
- **THEN** 不產生 snapshot

#### Scenario: snapshot 聚合內容
- **WHEN** snapshot 被觸發
- **THEN** snapshot 包含 `cefr_level`（眾數）、`avg_mtld`、`avg_vocd_d`、`vocabulary_size`、`strengths`、`weaknesses`、`conversation_count`
