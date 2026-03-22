## ADDED Requirements

### Requirement: Frontend router serves HTML pages
FastAPI SHALL 有獨立的 frontend router，回傳 Jinja2 TemplateResponse。

#### Scenario: Root path redirects to materials page
- **WHEN** 使用者訪問 `/`
- **THEN** 回傳素材管理頁面（或 redirect 到 `/materials`）

#### Scenario: Each section has its own route
- **WHEN** 使用者訪問 `/materials`、`/roleplay`、`/report`
- **THEN** 分別回傳對應的頁面 template，HTTP status 200

### Requirement: Static files served correctly
FastAPI SHALL mount `/static` 路徑，提供 CSS、JS、manifest、icon 等靜態檔案。

#### Scenario: Static CSS file accessible
- **WHEN** 瀏覽器請求 `/static/css/app.css`
- **THEN** 回傳 CSS 檔案，Content-Type 為 `text/css`

#### Scenario: Static JS file accessible
- **WHEN** 瀏覽器請求 `/static/js/app.js`
- **THEN** 回傳 JS 檔案，Content-Type 為 `application/javascript`

### Requirement: Jinja2 template engine configured
FastAPI app SHALL 設定 Jinja2Templates，template 目錄指向 `templates/`。

#### Scenario: Template rendering works
- **WHEN** frontend router 使用 TemplateResponse 渲染 `pages/materials.html`
- **THEN** 回傳完整的 HTML 頁面，包含 base template 的結構

### Requirement: Placeholder pages show section identity
每個 placeholder 頁面 SHALL 顯示該區塊的名稱和簡短說明，讓使用者知道自己在哪個區塊。

#### Scenario: Materials placeholder shows section name
- **WHEN** 使用者訪問 `/materials`
- **THEN** 頁面顯示「素材管理」標題和 placeholder 內容

#### Scenario: Roleplay placeholder shows section name
- **WHEN** 使用者訪問 `/roleplay`
- **THEN** 頁面顯示「Role Play」標題和 placeholder 內容

#### Scenario: Report placeholder shows section name
- **WHEN** 使用者訪問 `/report`
- **THEN** 頁面顯示「能力報告」標題和 placeholder 內容
