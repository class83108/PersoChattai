## ADDED Requirements

### Requirement: Crawl 執行結果模型
系統 SHALL 定義 `CrawlRunResult` Pydantic model，記錄單次 crawl 執行的統計資訊。

#### Scenario: 正常執行後回傳結果
- **WHEN** 爬蟲執行完成
- **THEN** 回傳 CrawlRunResult 包含：started_at、finished_at、sources（每個 source 的 new_count、skipped_count、failed_count）、total_new、total_skipped、total_failed

#### Scenario: 部分 source 失敗
- **WHEN** 爬蟲執行中某個 source 的 fetch_article_list 失敗
- **THEN** 該 source 的結果標記為 error（附錯誤訊息），其餘 source 照常執行，最終結果包含所有 source 的狀態

### Requirement: 單一 source 結果模型
系統 SHALL 定義 `SourceCrawlResult` Pydantic model，記錄單一 source 的爬取統計。

#### Scenario: source 執行成功
- **WHEN** 某個 source 爬取完成，新增 3 篇、跳過 7 篇、失敗 0 篇
- **THEN** SourceCrawlResult 包含 source_type、new_count=3、skipped_count=7、failed_count=0、error=None

#### Scenario: 個別文章 fetch 失敗
- **WHEN** 某篇文章的 fetch_article_content 拋出例外
- **THEN** 該文章計入 failed_count，爬蟲繼續處理下一篇，不中斷整個 source
