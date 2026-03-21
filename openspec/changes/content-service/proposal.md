## Why

學習迴圈的起點是素材輸入——使用者需要有內容才能開始 Role Play 對話。目前 Conversation Service 已完成，但沒有素材來源，對話無法啟動。Content Service 提供三種素材管道（Podcast 爬取、PDF 上傳、自由主題），經 Claude Agent 摘要後產出標準化卡片，作為下游 Conversation Service 和 Assessment Service 的輸入。

## What Changes

- 新增 Podcast 爬蟲（All Ears English + BBC 6 Minute English），定時爬取文章內容
- 新增 PDF 上傳 endpoint，解析文字內容並驗證（大小、長度）
- 新增自由主題 prompt endpoint，接受使用者輸入的主題描述
- 新增卡片生成 pipeline：三種素材來源 → Claude Agent（content_summarizer skill）→ 標準化卡片
- 新增卡片查詢 API（依 tag / 難度 / 來源 / 關鍵字篩選）
- 新增 APScheduler 排程整合，定時觸發爬蟲任務

## Capabilities

### New Capabilities
- `card-management`: 卡片 CRUD 與查詢（建立、讀取、篩選），包含卡片的 Pydantic schema 與 DB repository
- `podcast-scraper`: Podcast 爬蟲系統，Protocol-based adapter 設計，支援 All Ears English 與 BBC 6 Minute English
- `content-ingestion`: 素材輸入管道（PDF 上傳解析 + 自由主題 prompt）的輸入驗證與處理
- `content-summarizer`: Claude Agent 摘要 pipeline，將原始文字轉換為標準化卡片

### Modified Capabilities
（無既有 capability 需要修改）

## Impact

- **新增程式碼**：`src/persochattai/content/` 下新增 schemas、repository、scraper、service、router 模組
- **修改程式碼**：`app.py` 需整合 APScheduler lifespan；`agent_factory.py` 已有 content agent factory 可直接使用
- **新增依賴**：httpx（爬蟲 HTTP client）、APScheduler、PyPDF2 或 pdfplumber（PDF 解析）
- **API 新增**：`POST /api/content/upload-pdf`、`POST /api/content/free-topic`、`GET /api/content/cards`、`GET /api/content/cards/{id}`
- **依賴關係**：依賴 Foundation 的 DB pool、models、agent_factory；下游 Conversation Service 的 scenario_designer 將消費卡片資料
