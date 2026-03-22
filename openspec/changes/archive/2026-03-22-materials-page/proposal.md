## Why

素材管理頁面（`/materials`）目前只是 placeholder。使用者需要瀏覽學習素材卡片、篩選/搜尋、上傳 PDF 筆記、輸入自由主題。後端 API 已就緒（`/api/content/cards`、`/api/content/upload-pdf`、`/api/content/free-topic`），需要前端頁面來串接這些 API。

## What Changes

- 實作素材卡片列表，使用 HTMX 從 `/api/content/cards` 動態載入
- 卡片展開/收合：摘要、關鍵詞彙、對話片段
- 篩選功能：source_type、difficulty、tag
- 關鍵字搜尋
- 無限捲動 (infinite scroll) 或 load more 分頁
- PDF 上傳表單（呼叫 `/api/content/upload-pdf`）
- 自由主題輸入表單（呼叫 `/api/content/free-topic`）

## Capabilities

### New Capabilities
- `card-list`: 素材卡片列表渲染，支援 HTMX 動態載入、篩選、搜尋、分頁
- `card-detail`: 卡片展開/收合，顯示完整內容（摘要、關鍵詞彙、對話片段、難度、tags）
- `content-upload`: PDF 上傳與自由主題輸入表單，透過 HTMX 提交並即時顯示結果

### Modified Capabilities
（無既有 capability 需要修改）

## Impact

- **修改檔案**: `templates/pages/materials.html`（從 placeholder 改為完整頁面）
- **新增檔案**: `templates/partials/card_list.html`、`templates/partials/card_item.html`（HTMX partial templates）
- **新增路由**: frontend router 新增 HTML partial 回傳端點（供 HTMX 使用）
- **依賴**: 現有 `/api/content/*` API endpoints
