## ADDED Requirements

### Requirement: 手動觸發爬蟲 API
系統 SHALL 提供 `POST /api/content/trigger-crawl` endpoint，允許手動觸發爬蟲執行。

#### Scenario: 成功觸發完整爬蟲
- **WHEN** 呼叫 `POST /api/content/trigger-crawl` 且無 body
- **THEN** 系統對所有已註冊的 scraper 執行爬取流程，回傳 `CrawlRunResult`（含各 source 的 new/skipped/failed 計數）

#### Scenario: 指定 source_type 觸發
- **WHEN** 呼叫 `POST /api/content/trigger-crawl` 且 body 為 `{ "source_types": ["podcast_bbc"] }`
- **THEN** 系統只對指定的 source_type 執行爬取，其餘跳過

#### Scenario: 指定不存在的 source_type
- **WHEN** 呼叫 `POST /api/content/trigger-crawl` 且 body 包含不存在的 source_type
- **THEN** 系統回傳 HTTP 422，訊息包含無效的 source_type 名稱

### Requirement: Concurrent guard
系統 SHALL 防止同時多次觸發爬蟲。

#### Scenario: 爬蟲已在執行中時再次觸發
- **WHEN** 爬蟲正在執行中，另一個 `POST /api/content/trigger-crawl` 請求送達
- **THEN** 系統回傳 HTTP 409 Conflict，訊息為「爬蟲正在執行中，請稍後再試」

#### Scenario: 排程觸發與手動觸發衝突
- **WHEN** 排程正在執行爬蟲 job，手動觸發請求送達
- **THEN** 系統回傳 HTTP 409 Conflict（共用同一個 lock）
