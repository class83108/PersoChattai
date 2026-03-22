Feature: 手動觸發爬蟲 API
  作為管理者
  我想要透過 API 手動觸發爬蟲
  以便在開發調試或運營時即時執行爬取

  Rule: Happy path

    Scenario: 無 body 觸發全部 source
      Given CrawlService 已初始化且有 2 個 scraper
      And 每個 scraper 回傳 2 篇新文章
      When 發送 POST /api/content/trigger-crawl 無 body
      Then API 回應狀態碼為 200
      And 回應包含 2 個 source 的結果
      And 每個 source 的 new_count 為 2

    Scenario: 指定 source_type 只觸發特定來源
      Given CrawlService 已初始化且有 2 個 scraper
      And 每個 scraper 回傳 2 篇新文章
      When 發送 POST /api/content/trigger-crawl body 為 source_types ["podcast_bbc"]
      Then API 回應狀態碼為 200
      And 回應只包含 podcast_bbc 的結果

  Rule: Error / Failure

    Scenario: 爬蟲已在執行中時回傳 409
      Given CrawlService 已初始化
      And 爬蟲正在執行中
      When 發送 POST /api/content/trigger-crawl 無 body
      Then API 回應狀態碼為 409
      And 回應訊息為「爬蟲正在執行中，請稍後再試」

    Scenario: 某 scraper fetch 失敗仍回傳部分結果
      Given CrawlService 已初始化且有 2 個 scraper
      And 第一個 scraper 的 fetch_article_list 拋出例外
      And 第二個 scraper 回傳 2 篇新文章
      When 呼叫 run_crawl
      Then 結果包含第一個 source 的 error 訊息
      And 結果包含第二個 source 的 new_count 為 2

  Rule: Input boundary

    Scenario: 空 source_types 陣列視為觸發全部
      Given CrawlService 已初始化且有 2 個 scraper
      And 每個 scraper 回傳 1 篇新文章
      When 發送 POST /api/content/trigger-crawl body 為 source_types []
      Then API 回應狀態碼為 200
      And 回應包含 2 個 source 的結果

    Scenario: 不存在的 source_type 回傳 422
      Given CrawlService 已初始化
      When 發送 POST /api/content/trigger-crawl body 為 source_types ["nonexistent"]
      Then API 回應狀態碼為 422

  Rule: Edge cases

    Scenario: 排程與手動觸發共用 lock
      Given CrawlService 已初始化
      And 排程正在執行爬蟲 job
      When 發送 POST /api/content/trigger-crawl 無 body
      Then API 回應狀態碼為 409

    Scenario: 排程觸發時 lock 被佔用則跳過
      Given CrawlService 已初始化
      And 手動觸發正在執行中
      When 排程觸發 _scrape_job
      Then 記錄 warning log
      And 不拋出例外

  Rule: Output contract

    Scenario: CrawlRunResult 包含完整欄位
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 3 篇文章其中 1 篇已存在
      When 呼叫 run_crawl
      Then 結果包含 started_at 非 None
      And 結果包含 finished_at 非 None
      And 結果包含 total_new 為 2
      And 結果包含 total_skipped 為 1
      And 結果包含 total_failed 為 0
