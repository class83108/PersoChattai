## ADDED Requirements

### Requirement: Assessment history list
報告頁面 SHALL 顯示使用者的評估歷史列表。

#### Scenario: History loads via HTMX
- **WHEN** 報告頁面載入
- **THEN** 透過 HTMX 載入評估歷史列表

#### Scenario: History item shows key info
- **WHEN** 歷史列表載入完成
- **THEN** 每筆顯示日期、CEFR 等級、三維度分數摘要

#### Scenario: Empty history
- **WHEN** 沒有評估記錄
- **THEN** 顯示空狀態提示

### Requirement: Assessment detail expandable
每筆評估記錄 SHALL 可展開查看詳細內容。

#### Scenario: Expand assessment shows detail
- **WHEN** 使用者點擊展開一筆評估
- **THEN** 顯示完整的三維度分析、質性評估文字、NLP 量化指標
