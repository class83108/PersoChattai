## 1. Pydantic Models & Repository

- [ ] 1.1 定義 `SourceCrawlResult` 和 `CrawlRunResult` Pydantic models（schemas.py）
- [ ] 1.2 新增 `CardRepository.filter_existing_urls(urls) -> set[str]` 批次查詢方法
- [ ] 1.3 為 filter_existing_urls 寫 .feature + pytest-bdd 測試

## 2. CrawlService 核心邏輯

- [ ] 2.1 建立 `CrawlService` class，含 asyncio.Lock concurrent guard
- [ ] 2.2 實作 `run_crawl(source_types?)` 完整流程：list → dedup → fetch → summarize → insert
- [ ] 2.3 為 crawl dedup 邏輯寫 .feature + pytest-bdd 測試（mock scraper + repository）
- [ ] 2.4 為 concurrent guard 寫 .feature + pytest-bdd 測試

## 3. API Endpoint

- [ ] 3.1 新增 `POST /api/content/trigger-crawl` endpoint，呼叫 CrawlService
- [ ] 3.2 處理 source_type 驗證（422）與 lock 衝突（409）
- [ ] 3.3 為 trigger-crawl endpoint 寫 .feature + pytest-bdd 測試

## 4. Scheduler 整合

- [ ] 4.1 修改 `ContentScheduler._scrape_job()` 改為呼叫 CrawlService.run_crawl()
- [ ] 4.2 處理 lock 衝突時的 warning log + 跳過邏輯
- [ ] 4.3 在 app lifespan 中注入 CrawlService 到 scheduler 和 app.state

## 5. 品質驗證

- [ ] 5.1 執行 pytest 確認所有測試通過
- [ ] 5.2 執行 ruff check + ruff format + pyright 確認無問題
