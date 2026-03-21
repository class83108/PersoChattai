## Context

Content Service 是學習迴圈的起點，負責取得、處理、儲存學習素材。目前 Foundation 和 Conversation Service 已完成，但對話啟動需要卡片資料作為輸入。

現有基礎：
- `models.py` 已定義 `Card`、`KeywordEntry` Pydantic model
- `agent_factory.py` 已有 `create_content_agent()` + `CONTENT_SUMMARIZER` skill
- `content/router.py` 是空骨架
- httpx、beautifulsoup4、apscheduler 已在 dependencies 中

## Goals / Non-Goals

**Goals:**
- 實作三種素材輸入管道：Podcast 爬取、PDF 上傳、自由主題
- 建立 Protocol-based 爬蟲 adapter 設計，方便未來新增來源
- 卡片 CRUD + 篩選查詢 API
- Claude Agent 摘要 pipeline（content_summarizer skill）
- APScheduler 排程整合
- 輸入驗證與錯誤回饋

**Non-Goals:**
- 前端 UI（HTMX 頁面）
- 爬蟲反封鎖策略（rate limiting、proxy rotation）
- 卡片編輯 / 刪除 API（MVP 不需要）
- 全文搜尋（PostgreSQL full-text search）

## Decisions

### 1. 爬蟲 adapter 使用 Protocol + 策略模式

每個來源網站一個 adapter class，共用 `ScraperProtocol`。

```python
class ScraperProtocol(Protocol):
    source_type: str
    async def fetch_article_list(self) -> list[ArticleMeta]: ...
    async def fetch_article_content(self, url: str) -> RawArticle: ...
```

**理由**：design-doc 已指定 Protocol-based 設計。新增來源只需實作一個 class，不改現有程式碼。
**替代方案**：繼承 ABC → 但 Protocol 更 Pythonic 且不強制繼承。

### 2. 摘要 pipeline 先同步處理，不做 background task queue

PDF 上傳 / 自由主題 → 同步呼叫 Claude Agent → 回傳卡片。爬蟲則在 scheduler job 中批次處理。

**理由**：MVP 使用者量小（小圈子），Claude API 回應時間 2-5 秒可接受。引入 Celery/RQ 過度工程化。
**替代方案**：FastAPI BackgroundTasks → 但使用者需要立即看到卡片結果，不適合 fire-and-forget。

### 3. PDF 解析使用 pdfplumber

**理由**：文字提取品質優於 PyPDF2，且 API 簡潔。需新增 dependency。
**替代方案**：PyPDF2 → 文字提取常有亂碼；pymupdf → 太重。

### 4. 卡片查詢使用 SQL 動態篩選，不用 ORM

延續 conversation repository 的 asyncpg 直接查詢模式，用動態拼 WHERE 條件。

**理由**：保持與現有 repository 一致的風格。查詢場景有限（tag / difficulty / source_type / keyword），不需要 ORM。

### 5. 爬蟲去重策略：source_url UNIQUE

cards 表的 source_url 作為去重依據，INSERT 時用 ON CONFLICT DO NOTHING。

**理由**：簡單有效，不需要額外的 hash 或 visited 表。

## Risks / Trade-offs

- **爬蟲目標網站結構變更** → 每個 adapter 獨立，影響範圍小。加入基本的 HTML 結構驗證，parse 失敗時 log warning 而非 crash。
- **Claude API 摘要品質不穩定** → content_summarizer skill 的 instructions 已定義明確的輸出格式。MVP 先不做品質驗證 layer。
- **PDF 文字過長時 Claude context window** → 截斷至 5000 字（design-doc 已定義），截斷位置在句子邊界。
- **APScheduler 在單 worker 模式下的問題** → 使用 `AsyncIOScheduler`，與 FastAPI event loop 共用。多 worker 時需切換到外部 scheduler（但 MVP 單機部署）。

## Module Structure

```
src/persochattai/content/
├── router.py          # REST API endpoints
├── schemas.py         # Request/Response models, Protocol
├── repository.py      # cards 表 CRUD
├── service.py         # 摘要 pipeline 邏輯
├── scraper/
│   ├── __init__.py
│   ├── protocol.py    # ScraperProtocol + 共用 models
│   ├── allearsenglish.py
│   └── bbc.py
└── scheduler.py       # APScheduler 設定 + job 定義
```
