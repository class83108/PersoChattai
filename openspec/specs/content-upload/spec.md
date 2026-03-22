## ADDED Requirements

### Requirement: PDF upload form with HTMX
使用者 SHALL 能透過表單上傳 PDF，上傳後即時顯示生成的卡片。

#### Scenario: Upload PDF and see result
- **WHEN** 使用者選擇 PDF 檔案並送出上傳表單
- **THEN** 透過 HTMX POST 上傳，成功後在結果區域顯示生成的摘要卡片

#### Scenario: Upload shows loading state
- **WHEN** PDF 正在上傳和處理中
- **THEN** 顯示 loading 指示器（如 DaisyUI loading spinner）

#### Scenario: Upload error shows message
- **WHEN** 上傳失敗（檔案過大、格式錯誤）
- **THEN** 在結果區域顯示錯誤訊息

### Requirement: Free topic input form
使用者 SHALL 能輸入自由主題，提交後即時顯示生成的卡片。

#### Scenario: Submit free topic and see result
- **WHEN** 使用者輸入主題文字並送出
- **THEN** 透過 HTMX POST 提交，成功後在結果區域顯示生成的卡片

#### Scenario: Free topic validation
- **WHEN** 使用者提交空白主題
- **THEN** 表單阻止提交（HTML5 required 驗證）

### Requirement: Upload and free topic sections are collapsible
上傳區和自由主題區 SHALL 可收合，避免佔據太多版面。

#### Scenario: Sections default to collapsed
- **WHEN** 頁面載入
- **THEN** PDF 上傳區和自由主題區預設為收合狀態

#### Scenario: Expand upload section
- **WHEN** 使用者點擊「上傳 PDF」標題
- **THEN** 展開顯示上傳表單
