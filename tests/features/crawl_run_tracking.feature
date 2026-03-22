Feature: 爬蟲執行紀錄
  作為系統
  我想要記錄每次爬蟲執行的統計資訊
  以便掌握爬蟲的運作狀態

  Rule: Happy path

    Scenario: 正常執行回傳完整 CrawlRunResult
      Given CrawlService 已初始化且有 2 個 scraper
      And 第一個 scraper 回傳 3 篇新文章
      And 第二個 scraper 回傳 2 篇新文章
      When 呼叫 run_crawl
      Then 結果的 sources 包含 2 筆 SourceCrawlResult
      And 第一個 source 的 new_count 為 3
      And 第二個 source 的 new_count 為 2

  Rule: Error / Failure

    Scenario: 某 source 整個失敗不影響其餘
      Given CrawlService 已初始化且有 2 個 scraper
      And 第一個 scraper 的 fetch_article_list 拋出例外
      And 第二個 scraper 回傳 2 篇新文章
      When 呼叫 run_crawl
      Then 結果的 sources 包含 2 筆
      And 第一個 source 的 error 不為 None
      And 第二個 source 的 new_count 為 2

  Rule: Output contract

    Scenario: total 欄位等於各 source 加總
      Given CrawlService 已初始化且有 2 個 scraper
      And 第一個 scraper 產出 new_count 2 skipped_count 1 failed_count 0
      And 第二個 scraper 產出 new_count 1 skipped_count 3 failed_count 1
      When 呼叫 run_crawl
      Then 結果的 total_new 為 3
      And 結果的 total_skipped 為 4
      And 結果的 total_failed 為 1

    Scenario: 時間欄位非 None
      Given CrawlService 已初始化且有 1 個 scraper
      When 呼叫 run_crawl
      Then 結果的 started_at 非 None
      And 結果的 finished_at 非 None
      And finished_at 晚於或等於 started_at
