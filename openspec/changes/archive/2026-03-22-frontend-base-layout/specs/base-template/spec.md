## ADDED Requirements

### Requirement: Base HTML template with proper head configuration
base.html SHALL 包含完整的 HTML5 結構，包括 charset、viewport meta、title block、favicon、CSS/JS 載入。所有頁面 template SHALL 繼承此 base template。

#### Scenario: Page inherits base template
- **WHEN** 任一頁面 template 被渲染
- **THEN** 產出的 HTML 包含完整的 `<!DOCTYPE html>` 結構、viewport meta tag、以及 Tailwind CSS / DaisyUI / HTMX 的載入標籤

#### Scenario: Page title is customizable
- **WHEN** 子頁面設定 title block
- **THEN** 瀏覽器標題顯示 `{page_title} | PersoChattai`

### Requirement: Tailwind CSS and DaisyUI loaded via CDN
base.html SHALL 透過 CDN 載入 Tailwind CSS 和 DaisyUI，確保所有 utility class 和元件 class 可用。

#### Scenario: DaisyUI components render correctly
- **WHEN** 頁面使用 DaisyUI class（如 `btn`、`card`）
- **THEN** 元件正確渲染並有對應的視覺樣式

### Requirement: HTMX loaded and configured
base.html SHALL 載入 HTMX library，並啟用 `hx-boost` 於主要內容區域。

#### Scenario: HTMX is available globally
- **WHEN** 頁面載入完成
- **THEN** `htmx` 物件存在於 window scope

### Requirement: PWA manifest linked
base.html SHALL 連結 PWA manifest.json，包含 app name、icons、theme color。

#### Scenario: Manifest is accessible
- **WHEN** 瀏覽器請求 `/static/manifest.json`
- **THEN** 回傳有效的 Web App Manifest，包含 `name`、`short_name`、`start_url`、`display`、`icons` 欄位

### Requirement: Content block for page-specific content
base.html SHALL 定義 `content` block，供子 template 填入頁面內容。

#### Scenario: Child template fills content block
- **WHEN** 子 template 定義 `{% block content %}` 區塊
- **THEN** 該內容出現在 nav 和 footer 之間的主要區域
