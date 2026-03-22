## ADDED Requirements

### Requirement: CEFR level badge display
能力概覽 SHALL 顯示使用者當前的 CEFR 等級（A1-C2）。

#### Scenario: CEFR level shown
- **WHEN** 概覽區載入完成且有進度資料
- **THEN** 顯示 CEFR 等級 badge

#### Scenario: No data yet
- **WHEN** 使用者沒有任何評估記錄
- **THEN** 顯示「尚無評估資料，完成一場 Role Play 後即可查看」

### Requirement: Three dimension scores
概覽區 SHALL 顯示三個維度的分數：Lexical Resource、Fluency & Coherence、Grammatical Range & Accuracy。

#### Scenario: Dimension scores as progress bars
- **WHEN** 概覽區載入完成且有進度資料
- **THEN** 三個維度各顯示名稱、分數數值、progress bar
