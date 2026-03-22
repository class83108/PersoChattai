## 1. 專案設定與依賴

- [x] 1.1 新增 `jinja2` 依賴到 pyproject.toml
- [x] 1.2 建立目錄結構：`templates/pages/`、`static/css/`、`static/js/`、`static/icons/`

## 2. FastAPI 靜態檔案與 Template 引擎

- [x] 2.1 在 `app.py` 設定 `StaticFiles` mount 到 `/static`
- [x] 2.2 設定 `Jinja2Templates` 指向 `templates/` 目錄

## 3. Base Template

- [x] 3.1 建立 `templates/base.html`：HTML5 結構、viewport meta、title block
- [x] 3.2 在 base.html 載入 Tailwind CSS + DaisyUI（CDN）
- [x] 3.3 在 base.html 載入 HTMX（CDN）
- [x] 3.4 在 base.html 定義 `content` block 與基礎 layout 結構
- [x] 3.5 連結 `static/css/app.css` 與 `static/js/app.js`

## 4. Navigation

- [x] 4.1 在 base.html 建立 desktop 頂部 navbar（DaisyUI navbar 元件）
- [x] 4.2 在 base.html 建立 mobile 底部 navigation bar
- [x] 4.3 實作 active state 標示（根據當前 URL highlight 對應連結）
- [x] 4.4 設定 `hx-boost="true"` 於主要內容區域

## 5. Placeholder 頁面

- [x] 5.1 建立 `templates/pages/materials.html`（繼承 base，顯示「素材管理」標題）
- [x] 5.2 建立 `templates/pages/roleplay.html`（繼承 base，顯示「Role Play」標題）
- [x] 5.3 建立 `templates/pages/report.html`（繼承 base，顯示「能力報告」標題）

## 6. 頁面路由

- [x] 6.1 建立 `src/persochattai/frontend/router.py`，定義三個頁面路由 + root redirect
- [x] 6.2 在 `app.py` 註冊 frontend router

## 7. PWA Manifest

- [x] 7.1 建立 `static/manifest.json`（name、short_name、start_url、display、theme_color、icons）
- [x] 7.2 在 base.html 的 `<head>` 加入 manifest link

## 8. 靜態資源

- [x] 8.1 建立 `static/css/app.css`（最小化自定義樣式）
- [x] 8.2 建立 `static/js/app.js`（HTMX 設定、共用行為）
