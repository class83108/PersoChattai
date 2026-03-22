## 1. Partial Templates 基礎

- [x] 1.1 建立 `templates/partials/` 目錄
- [x] 1.2 建立 `templates/partials/card_item.html`（收合狀態：標題 + source badge + difficulty badge）
- [x] 1.3 建立 `templates/partials/card_list.html`（卡片列表 + load more 按鈕邏輯）

## 2. Frontend Router — Partial 端點

- [x] 2.1 新增 `GET /materials/partials/card-list` 端點（呼叫 content API，渲染 card_list partial）
- [x] 2.2 新增 `GET /materials/partials/card-item/{card_id}` 端點（渲染展開的卡片 partial）

## 3. 素材管理頁面重構

- [x] 3.1 重寫 `templates/pages/materials.html`：加入篩選區、搜尋框、卡片列表容器、上傳/主題區
- [x] 3.2 篩選表單：source_type select + difficulty select，`hx-get` + `hx-trigger="change"`
- [x] 3.3 搜尋框：`hx-get` + `hx-trigger="keyup changed delay:300ms"`
- [x] 3.4 卡片列表容器：`hx-get` 初始載入 + `hx-trigger="load"`

## 4. 卡片展開/收合

- [x] 4.1 使用 DaisyUI collapse 元件實作卡片展開/收合
- [x] 4.2 展開狀態顯示：摘要、關鍵詞彙（詞彙 — 解釋）、對話片段、tags
- [x] 4.3 無關鍵詞彙/對話片段時隱藏對應區塊

## 5. Load More 分頁

- [x] 5.1 card_list partial 判斷是否有更多卡片，條件顯示 load more 按鈕
- [x] 5.2 Load more 按鈕使用 `hx-get` + `hx-swap="afterend"` 追加卡片

## 6. 內容上傳區

- [x] 6.1 建立 `templates/partials/upload_result.html`（上傳/主題結果 fragment）
- [x] 6.2 PDF 上傳表單：`hx-post` + `hx-encoding="multipart/form-data"` + loading 指示器
- [x] 6.3 自由主題輸入表單：`hx-post` + 結果顯示
- [x] 6.4 新增 `POST /materials/upload-pdf` partial 端點（代理 API + 渲染結果）
- [x] 6.5 新增 `POST /materials/free-topic` partial 端點（代理 API + 渲染結果）
- [x] 6.6 上傳區和主題區使用 DaisyUI collapse 預設收合
