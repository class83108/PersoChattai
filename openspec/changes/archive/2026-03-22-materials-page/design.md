## Context

素材管理頁面需要串接已有的 Content Service API。後端已提供：
- `GET /api/content/cards` — 列表查詢，支援 source_type / difficulty / tag / keyword / limit / offset 篩選
- `GET /api/content/cards/{card_id}` — 單張卡片詳情
- `POST /api/content/upload-pdf` — PDF 上傳，回傳生成的卡片
- `POST /api/content/free-topic` — 自由主題，回傳生成的卡片

卡片結構包含：標題、摘要、關鍵詞彙（含解釋）、對話片段、難度標籤（CEFR）、tags、來源類型/URL。

前端使用 HTMX，核心模式是：前端 route 回傳 HTML partial，HTMX swap 到頁面中。

## Goals / Non-Goals

**Goals:**
- 用 HTMX 實作卡片列表的動態載入（不需整頁刷新）
- 篩選/搜尋時 HTMX 替換卡片列表區域
- 卡片展開/收合顯示完整內容
- PDF 上傳後即時顯示生成的卡片
- 自由主題輸入後即時顯示生成的卡片
- Load more 分頁（而非 infinite scroll，避免複雜度）

**Non-Goals:**
- 不做卡片編輯/刪除功能
- 不做拖拽排序
- 不做離線快取卡片
- 不做卡片收藏/標記功能

## Decisions

### 1. HTMX Partial Templates 模式

前端 router 新增 partial 端點（回傳 HTML fragment 而非完整頁面），供 HTMX `hx-get` 使用。

```
GET /materials/partials/card-list   → 回傳卡片列表 HTML fragment
GET /materials/partials/card-item/{id} → 回傳單張展開卡片 HTML fragment
```

這些 partial 端點內部呼叫 `/api/content/cards` JSON API，拿到資料後用 Jinja2 template 渲染成 HTML fragment。

替代方案：直接讓 HTMX 呼叫 JSON API → HTMX 設計為 HTML-first，處理 JSON 需要額外 JS，違反 HTMX 哲學。

### 2. 卡片展開/收合：DaisyUI collapse

使用 DaisyUI 的 `collapse` 元件，純 CSS 實作展開/收合，不需要 JS 也不需要額外 HTMX 請求。

卡片收合時顯示：標題、來源類型 badge、難度 badge。
卡片展開時額外顯示：摘要、關鍵詞彙表、對話片段、tags。

### 3. 篩選：HTMX form + hx-get

篩選表單使用 `hx-get="/materials/partials/card-list"` + `hx-trigger="change"` + `hx-include`，每次篩選變更自動重新載入卡片列表。

搜尋框使用 `hx-trigger="keyup changed delay:300ms"` 做 debounce。

### 4. 檔案上傳：hx-post + hx-encoding

PDF 上傳使用 `hx-post` + `hx-encoding="multipart/form-data"`，上傳後將結果 swap 到結果區域。
自由主題使用 `hx-post` + JSON body。

兩者都在 frontend router 加 partial 端點來代理 API 呼叫並渲染結果 HTML。

### 5. 目錄結構

```
templates/
  pages/
    materials.html          # 完整頁面（篩選 + 列表 + 上傳區）
  partials/
    card_list.html          # 卡片列表 fragment（含 load more 按鈕）
    card_item.html          # 單張卡片 fragment
    card_item_expanded.html # 展開的卡片 fragment
    upload_result.html      # 上傳/主題結果 fragment
```

## Risks / Trade-offs

- **Partial 端點代理 API** → 增加一層間接呼叫。Mitigation：這是 HTMX 標準模式，保持 HTML-first 的一致性，且可在 partial 端點加入前端特定邏輯（如格式化、i18n）。
- **篩選 debounce** → 快速輸入可能產生多次請求。Mitigation：HTMX 內建 `delay` 支援，300ms 足夠。
- **大量卡片效能** → Load more 每次載入 20 張，DOM 會持續增長。Mitigation：目前使用規模小（小圈子），不是問題。
