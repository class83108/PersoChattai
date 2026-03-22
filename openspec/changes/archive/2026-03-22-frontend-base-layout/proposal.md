## Why

目前專案只有後端 API，沒有任何前端頁面。使用者無法透過瀏覽器與系統互動。需要建立 PWA 的基礎頁面架構（base template、navigation、responsive layout），作為後續三大功能區塊（素材管理、Role Play 對話、能力報告）的基礎。

## What Changes

- 新增 FastAPI 靜態檔案服務與 Jinja2 template 引擎設定
- 新增 base template（含 HTML head、nav、footer、HTMX/Tailwind/DaisyUI 載入）
- 新增 responsive navigation（三個主要區塊的切換）
- 新增三個 placeholder 頁面（素材管理、Role Play、能力報告）
- 新增 PWA manifest 與 service worker 基礎設定
- 新增頁面路由（FastAPI route 回傳 HTML template）

## Capabilities

### New Capabilities
- `base-template`: 基礎 HTML template 架構，包含 head meta、CSS/JS 載入、共用 layout blocks、PWA manifest
- `navigation`: 響應式導航列，支援三大區塊切換，mobile-first 設計，active state 指示
- `page-routing`: FastAPI 頁面路由，Jinja2 template 渲染，靜態檔案服務設定

### Modified Capabilities
（無既有 capability 需要修改）

## Impact

- **新增目錄**: `templates/`, `static/css/`, `static/js/`, `static/icons/`
- **修改檔案**: `src/persochattai/app.py`（加入 static mount 和 template routes）
- **新增依賴**: `jinja2`（FastAPI template 引擎）
- **CDN 依賴**: Tailwind CSS、DaisyUI、HTMX（透過 CDN 載入，後續可改為本地打包）
