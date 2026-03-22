## ADDED Requirements

### Requirement: Vocabulary statistics display
報告頁面 SHALL 顯示詞彙統計資訊。

#### Scenario: Vocabulary stats shown
- **WHEN** 詞彙統計區載入完成
- **THEN** 顯示累計詞彙量、新詞出現率等統計

#### Scenario: No vocabulary data
- **WHEN** 沒有詞彙記錄
- **THEN** 顯示「尚無詞彙資料」

### Requirement: API usage summary display
報告頁面 SHALL 顯示 API 用量摘要。

#### Scenario: Usage summary shown
- **WHEN** 用量區載入完成
- **THEN** 顯示 token 使用量、費用等資訊
