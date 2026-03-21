## 1. Schemas + Repository

- [x] 1.1 建立 content/schemas.py — CardFilter（查詢篩選）、CreateCardRequest、UploadPdfResponse、FreeTopicRequest、CardRepositoryProtocol
- [x] 1.2 建立 content/repository.py — CardRepository（create、get_by_id、list_cards with filters、exists_by_url）

## 2. Scraper 系統

- [x] 2.1 建立 content/scraper/protocol.py — ScraperProtocol、ArticleMeta、RawArticle、ScraperError
- [x] 2.2 建立 content/scraper/allearsenglish.py — AllEarsEnglishScraper（fetch_article_list、fetch_article_content）
- [x] 2.3 建立 content/scraper/bbc.py — BBC6MinuteEnglishScraper（fetch_article_list、fetch_article_content）

## 3. Content Service（摘要 pipeline）

- [x] 3.1 建立 content/service.py — ContentService 骨架（summarize_article、summarize_pdf、summarize_free_topic）
- [x] 3.2 實作 Claude Agent 摘要整合（呼叫 content_summarizer skill → 解析回傳 → 建立卡片）
- [x] 3.3 實作 PDF 文字解析（pdfplumber）+ 截斷邏輯（5000 字句子邊界）

## 4. REST API Endpoints

- [x] 4.1 實作 GET /api/content/cards — 卡片列表查詢（支援 source_type、difficulty、tag、keyword、分頁）
- [x] 4.2 實作 GET /api/content/cards/{card_id} — 單一卡片查詢
- [x] 4.3 實作 POST /api/content/upload-pdf — PDF 上傳（大小驗證、解析、摘要）
- [x] 4.4 實作 POST /api/content/free-topic — 自由主題提交

## 5. Scheduler 整合

- [x] 5.1 建立 content/scheduler.py — APScheduler AsyncIOScheduler 設定 + scrape job 定義
- [x] 5.2 整合至 app.py lifespan — 啟動時註冊 scheduler，關閉時 shutdown

## 6. 驗證

- [x] 6.1 撰寫 .feature 檔（card-management、podcast-scraper、content-ingestion、content-summarizer）
- [x] 6.2 撰寫 pytest-bdd step definitions
- [x] 6.3 確認 ruff check + ruff format + pyright 全部通過
- [x] 6.4 Design review
