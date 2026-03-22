## ADDED Requirements

### Requirement: Desktop top navigation bar
Desktop 視窗 SHALL 顯示頂部 navbar，包含 app logo/名稱及三個主要區塊連結：素材管理、Role Play、能力報告。

#### Scenario: Desktop navbar displays all navigation items
- **WHEN** 使用者在 desktop 視窗（≥ 768px）瀏覽頁面
- **THEN** 頂部顯示 navbar，包含三個可點擊的導航連結

### Requirement: Mobile bottom navigation bar
Mobile 視窗 SHALL 顯示底部 navigation bar，包含三個主要區塊的 icon + label。

#### Scenario: Mobile bottom nav displays on small screens
- **WHEN** 使用者在 mobile 視窗（< 768px）瀏覽頁面
- **THEN** 底部顯示固定的 navigation bar，頂部 navbar 僅顯示 app 名稱

### Requirement: Active state indication
Navigation SHALL 標示當前所在頁面的對應連結為 active 狀態。

#### Scenario: Current page link is highlighted
- **WHEN** 使用者位於素材管理頁面
- **THEN** 素材管理的 nav 連結顯示 active 樣式（與其他連結視覺上有區別）

### Requirement: Navigation uses hx-boost for SPA-like transitions
Navigation 連結 SHALL 使用 `hx-boost="true"` 實現無整頁重載的頁面切換。

#### Scenario: Page transition without full reload
- **WHEN** 使用者點擊 nav 連結切換頁面
- **THEN** 頁面內容更新但不觸發完整頁面重載（URL 更新、瀏覽器不閃白）
