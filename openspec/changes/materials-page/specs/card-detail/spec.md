## ADDED Requirements

### Requirement: Card collapsed view shows summary info
每張卡片的收合狀態 SHALL 顯示標題、來源類型 badge、難度 badge。

#### Scenario: Collapsed card displays key info
- **WHEN** 卡片處於收合狀態
- **THEN** 顯示卡片標題、來源類型標籤（如 podcast / pdf / free_topic）、難度標籤（CEFR 等級）

### Requirement: Card expands to show full content
使用者 SHALL 能展開卡片查看完整內容，包含摘要、關鍵詞彙、對話片段、tags。

#### Scenario: Expand card shows all fields
- **WHEN** 使用者點擊卡片展開
- **THEN** 顯示完整摘要（3-5 句）、關鍵詞彙列表（含解釋）、對話片段（如有）、tags 列表

#### Scenario: Collapse card hides detail
- **WHEN** 使用者點擊已展開的卡片
- **THEN** 卡片收合回僅顯示標題和 badges 的狀態

### Requirement: Keywords display with explanation
關鍵詞彙 SHALL 以結構化方式顯示，包含詞彙本身和解釋。

#### Scenario: Keywords render as definition list
- **WHEN** 卡片展開且有關鍵詞彙
- **THEN** 每個詞彙顯示為「詞彙 — 解釋」的格式

#### Scenario: No keywords section when empty
- **WHEN** 卡片沒有關鍵詞彙
- **THEN** 不顯示關鍵詞彙區塊
