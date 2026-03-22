## Why

目前爬蟲只能透過 APScheduler 每 6 小時自動觸發，無法手動執行，開發調試與運營操作不便。此外 `_scrape_job()` 尚未串接實際邏輯，且每次執行會對所有文章重複呼叫 `fetch_article_content` + Claude summarize，浪費 API quota。需要補上手動觸發入口並實作高效的去重流程。

## What Changes

- 新增 `POST /api/content/trigger-crawl` endpoint，支援手動觸發爬蟲，可指定 `source_type` 篩選來源
- 加入 concurrent guard，防止同時多次觸發爬蟲
- 實作 `_scrape_job` 完整流程：fetch_article_list → 批次 URL 去重 → fetch_article_content → summarize → insert
- 在 fetch_article_list 之後、fetch_article_content 之前，批次查詢 DB 過濾已存在的 URL，避免不必要的網路請求與 LLM 呼叫
- 新增 crawl run 紀錄（開始/結束時間、各 source 新增/跳過/失敗數量），供 API 回傳與日後查詢

## Capabilities

### New Capabilities
- `crawl-trigger`: 手動觸發爬蟲的 API endpoint，含 concurrent guard 與執行結果回傳
- `crawl-dedup`: 爬蟲去重邏輯，在 fetch content 前批次過濾已存在 URL
- `crawl-run-tracking`: 爬蟲執行紀錄，追蹤每次 crawl 的統計資訊

### Modified Capabilities
- `podcast-scraper`: 排程執行爬蟲 job 的 requirement 需更新，加入去重前置步驟與 crawl run 紀錄

## Impact

- **API**: 新增 1 個 endpoint (`POST /api/content/trigger-crawl`)
- **DB**: 可能新增 `crawl_runs` 表（或以 in-memory 紀錄回傳）
- **Code**: `scheduler.py` 需串接完整 scrape 流程；`repository.py` 需新增批次 URL 存在檢查方法
- **依賴**: 無新增外部依賴，使用既有的 APScheduler + SQLAlchemy + httpx
