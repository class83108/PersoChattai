## ADDED Requirements

### Requirement: Card list loads dynamically via HTMX
素材管理頁面載入時 SHALL 透過 HTMX 從 partial 端點載入卡片列表，不需等待完整頁面重載。

#### Scenario: Initial page load fetches cards
- **WHEN** 使用者訪問 `/materials`
- **THEN** 頁面自動透過 `hx-get` 載入卡片列表到指定容器

#### Scenario: Empty state when no cards exist
- **WHEN** 卡片列表為空
- **THEN** 顯示空狀態提示（如「目前沒有素材，上傳 PDF 或輸入主題來建立」）

### Requirement: Filter cards by source type and difficulty
使用者 SHALL 能透過篩選條件（source_type、difficulty）即時更新卡片列表。

#### Scenario: Filter by source type
- **WHEN** 使用者選擇 source_type 篩選（如 podcast、pdf、free_topic）
- **THEN** 卡片列表更新為僅顯示該來源類型的卡片

#### Scenario: Filter by difficulty
- **WHEN** 使用者選擇 difficulty 篩選（CEFR 等級）
- **THEN** 卡片列表更新為僅顯示該難度的卡片

#### Scenario: Multiple filters combine
- **WHEN** 使用者同時設定 source_type 和 difficulty
- **THEN** 卡片列表顯示同時符合兩個條件的卡片

### Requirement: Search cards by keyword
使用者 SHALL 能輸入關鍵字搜尋卡片，搜尋有 debounce 避免過多請求。

#### Scenario: Keyword search with debounce
- **WHEN** 使用者在搜尋框輸入關鍵字
- **THEN** 等待 300ms 無新輸入後，卡片列表更新為匹配的結果

#### Scenario: Clear search shows all cards
- **WHEN** 使用者清空搜尋框
- **THEN** 卡片列表恢復為未篩選的完整列表

### Requirement: Load more pagination
卡片列表 SHALL 支援 load more 分頁，每次載入固定數量的卡片。

#### Scenario: Load more button appears when more cards exist
- **WHEN** 卡片列表載入完成且還有更多卡片
- **THEN** 列表底部顯示「載入更多」按鈕

#### Scenario: Load more appends cards
- **WHEN** 使用者點擊「載入更多」
- **THEN** 新的卡片追加到現有列表下方，不替換已有卡片

#### Scenario: No load more when all cards loaded
- **WHEN** 已載入的卡片數量少於 limit（表示沒有更多）
- **THEN** 不顯示「載入更多」按鈕
