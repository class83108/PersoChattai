## Context

目前 PersoChattai 只有 FastAPI JSON API，沒有任何前端頁面。使用者需要透過瀏覽器操作三大功能：素材管理、Role Play 對話、能力報告。北極星文檔定義技術棧為 HTMX + vanilla JS 的 PWA，需要建立基礎 layout 作為所有頁面的骨架。

現有 `app.py` 已掛載四個 API router（content、conversation、assessment、usage），但沒有 template 引擎和靜態檔案服務。

## Goals / Non-Goals

**Goals:**
- 建立可複用的 base template（Jinja2），包含完整 HTML head 和共用 layout
- 建立 responsive navigation，支援 mobile 和 desktop
- 設定 Tailwind CSS + DaisyUI（CDN 方式）
- 設定 HTMX 載入
- 建立 PWA manifest 基礎
- 建立三個 placeholder 頁面，確認路由和 template 繼承正常運作

**Non-Goals:**
- 不實作任何業務功能（素材卡片、對話介面、報告圖表）
- 不做 Tailwind CSS 本地打包（先用 CDN，後續優化）
- 不做使用者認證
- 不做 service worker 離線快取邏輯
- 不做深色/淺色模式切換（DaisyUI theme 先固定一個）

## Decisions

### 1. Template 引擎：Jinja2

FastAPI 原生支援 Jinja2Templates，與 HTMX 的 HTML-first 理念一致。不需要額外前端框架。

### 2. CSS 框架：Tailwind CSS + DaisyUI（CDN）

- Tailwind 提供 utility-first CSS
- DaisyUI 提供語義化元件 class（`btn`、`card`、`navbar`），減少 class 堆疊
- 先用 CDN 快速開始，避免 build pipeline 的複雜度
- 替代方案考量：純 Tailwind 需要大量 class 組合，DaisyUI 降低工作量且提供內建 theme 系統

### 3. 目錄結構

```
templates/
  base.html          # 基礎 layout（head + nav + content block + footer）
  pages/
    materials.html    # 素材管理 placeholder
    roleplay.html     # Role Play placeholder
    report.html       # 能力報告 placeholder
static/
  css/
    app.css           # 自定義樣式（少量，主要靠 Tailwind/DaisyUI）
  js/
    app.js            # 共用 JS（HTMX 設定、共用行為）
  manifest.json       # PWA manifest
  icons/              # PWA icons
```

### 4. 路由設計：獨立 frontend router

新增 `src/persochattai/frontend/router.py`，與 API router 分離。頁面路由回傳 `TemplateResponse`，不與既有 API router 混合。

替代方案：直接在 `app.py` 加路由 → 職責不清，app.py 已經夠長。

### 5. Navigation：DaisyUI navbar + bottom navigation

- Desktop：頂部 navbar，三個主要連結
- Mobile：底部 bottom navigation bar（thumb-friendly），搭配頂部簡化 navbar
- 使用 HTMX `hx-boost` 讓頁面切換不需整頁重載

## Risks / Trade-offs

- **CDN 依賴** → 離線時 CSS/JS 無法載入。Mitigation：PWA service worker 可快取 CDN 資源，後續改本地打包。
- **DaisyUI theme 鎖定** → 後續切換 theme 可能需要調整自定義樣式。Mitigation：自定義樣式最小化，盡量用 DaisyUI 語義 class。
- **hx-boost 與 SPA-like 行為** → 部分頁面可能需要完整重載（如 WebRTC）。Mitigation：Role Play 頁面可排除 hx-boost。
