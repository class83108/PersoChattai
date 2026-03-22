## Context

目前 `ContentScheduler._scrape_job()` 只有一行 log，尚未串接實際爬蟲流程。爬蟲沒有 API 入口可手動觸發，且每次排程會對所有文章重複處理，浪費 Claude API quota。

現有元件：
- `ScraperProtocol` + 兩個實作（AllEarsEnglish、BBC）
- `CardRepository` 已有 `exists_by_url()` 和 `ON CONFLICT DO NOTHING`
- `ContentService.summarize_article()` 負責呼叫 Claude 產出摘要卡片
- `ContentScheduler` 用 APScheduler interval trigger

## Goals / Non-Goals

**Goals:**
- 提供 API endpoint 手動觸發爬蟲，回傳執行摘要
- 實作 `_scrape_job` 完整流程，含批次 URL 去重
- 追蹤每次 crawl run 的統計資訊

**Non-Goals:**
- 不做 crawl queue / 分散式排程（單機即可）
- 不做 crawl 歷史查詢 API（本次只追蹤最近一次執行）
- 不做 webhook / callback 通知
- 不改 scraper adapter 本身的邏輯

## Decisions

### D1: Crawl 執行邏輯抽成獨立 service function

**選擇**: 將 crawl 核心邏輯抽成 `CrawlService.run_crawl(source_types?)` async method，scheduler 和 API endpoint 都呼叫它。

**替代方案**: 把邏輯直接寫在 scheduler 裡，API 呼叫 scheduler.trigger()
→ 拒絕：scheduler 不應該承擔業務邏輯，且測試困難

### D2: 批次 URL 去重用一次查詢

**選擇**: 新增 `CardRepository.filter_existing_urls(urls: list[str]) -> set[str]`，用 `SELECT source_url FROM cards WHERE source_url IN (...)` 一次查出已存在的 URL，再取差集得到需要爬取的新 URL。

**替代方案**: 逐一呼叫 `exists_by_url()`
→ 拒絕：N+1 查詢，每個 source 通常有 10-30 篇文章

### D3: Concurrent guard 用 asyncio.Lock

**選擇**: `CrawlService` 持有一個 `asyncio.Lock`，`run_crawl` 入口用 `lock.acquire(blocking=False)` 嘗試取鎖，失敗就回傳 409 Conflict。

**替代方案**: 用 DB row lock 或 Redis lock
→ 拒絕：單機部署，asyncio.Lock 夠用且無外部依賴

### D4: Crawl run 紀錄用 Pydantic model 回傳，不存 DB

**選擇**: `run_crawl()` 回傳 `CrawlRunResult` Pydantic model，包含各 source 的 new/skipped/failed 計數與耗時。API endpoint 直接回傳此 model。暫不存 DB。

**替代方案**: 新增 `crawl_runs` DB 表
→ 延後：目前只需要即時結果，未來有需求再加 DB 紀錄

### D5: API endpoint 設計

**選擇**: `POST /api/content/trigger-crawl`，body 可選 `{ "source_types": ["podcast_allearsenglish"] }` 篩選來源。回傳 `CrawlRunResult`。

因為 crawl 可能耗時數十秒（需呼叫 Claude），endpoint 直接 await 完成後回傳結果（同步風格）。前端可設較長 timeout。

## Risks / Trade-offs

- **[長時間 request]** crawl 可能耗時 30s+（多篇文章 × Claude API）→ 先接受，未來可改為 background task + polling
- **[Lock 範圍]** asyncio.Lock 在 worker restart 後消失 → 單機可接受，不會造成資料損壞（DB 層仍有 ON CONFLICT）
- **[記憶體]** CrawlRunResult 不存 DB，重啟後遺失 → 可接受，主要用途是 API 即時回傳
