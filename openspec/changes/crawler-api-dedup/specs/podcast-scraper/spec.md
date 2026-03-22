## MODIFIED Requirements

### Requirement: 排程執行爬蟲 job
系統 SHALL 使用 APScheduler 定時執行爬蟲任務。排程觸發時，系統 SHALL 透過 CrawlService 執行完整爬取流程（含批次 URL 去重），而非直接在 scheduler 中實作業務邏輯。

#### Scenario: 排程啟動
- **WHEN** FastAPI app 啟動
- **THEN** APScheduler 註冊爬蟲 job，以設定的 interval 定時執行

#### Scenario: 排程執行爬蟲 job
- **WHEN** 排程觸發爬蟲 job
- **THEN** 系統透過 CrawlService.run_crawl() 執行：fetch_article_list → 批次 URL 去重 → 只對新 URL 執行 fetch_article_content → summarize → insert，結果記錄於 log

#### Scenario: app 關閉時清理 scheduler
- **WHEN** FastAPI app 關閉
- **THEN** APScheduler 正確 shutdown，不殘留背景任務

#### Scenario: 排程執行時 lock 衝突
- **WHEN** 排程觸發爬蟲 job 但 CrawlService 的 lock 已被佔用（手動觸發正在執行）
- **THEN** 排程 job 記錄 warning log 並跳過本次執行，不拋出例外
