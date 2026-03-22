Feature: 爬蟲批次去重
  作為系統
  我想要在爬取文章內容前過濾已存在的 URL
  以便節省網路請求與 Claude API 用量

  Rule: Happy path

    Scenario: 部分新 URL 只爬新的
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 5 篇文章
      And 其中 3 篇的 source_url 已存在於 DB
      When 呼叫 run_crawl
      Then fetch_article_content 只被呼叫 2 次
      And 結果中該 source 的 new_count 為 2
      And 結果中該 source 的 skipped_count 為 3

    Scenario: 全部是新 URL
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 3 篇文章
      And 所有 source_url 都不存在於 DB
      When 呼叫 run_crawl
      Then fetch_article_content 被呼叫 3 次
      And 結果中該 source 的 new_count 為 3
      And 結果中該 source 的 skipped_count 為 0

    Scenario: 全部已存在
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 3 篇文章
      And 所有 source_url 都已存在於 DB
      When 呼叫 run_crawl
      Then fetch_article_content 不被呼叫
      And 結果中該 source 的 new_count 為 0
      And 結果中該 source 的 skipped_count 為 3

  Rule: Error / Failure

    Scenario: 個別文章 fetch 失敗繼續處理下一篇
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 3 篇新文章
      And 第 2 篇的 fetch_article_content 拋出例外
      When 呼叫 run_crawl
      Then 結果中該 source 的 new_count 為 2
      And 結果中該 source 的 failed_count 為 1

  Rule: Input boundary

    Scenario: fetch_article_list 回傳空列表
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 0 篇文章
      When 呼叫 run_crawl
      Then fetch_article_content 不被呼叫
      And 結果中該 source 的 new_count 為 0
      And 結果中該 source 的 skipped_count 為 0

    Scenario: filter_existing_urls 傳入空列表
      Given 測試用 CardRepository 已初始化
      When 呼叫 filter_existing_urls 傳入空列表
      Then 回傳空 set

  Rule: State mutation

    Scenario: 新卡片確實寫入 DB
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 2 篇新文章
      When 呼叫 run_crawl
      Then DB 中新增 2 張卡片

    Scenario: 重複執行不產生重複卡片
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 2 篇文章
      And 第一次 run_crawl 已執行完成
      When 再次呼叫 run_crawl
      Then 第二次結果中 new_count 為 0
      And 第二次結果中 skipped_count 為 2

  Rule: Output contract

    Scenario: new + skipped + failed 等於文章總數
      Given CrawlService 已初始化且有 1 個 scraper
      And scraper 回傳 5 篇文章其中 2 篇已存在且 1 篇 fetch 會失敗
      When 呼叫 run_crawl
      Then 結果中該 source 的 new_count + skipped_count + failed_count 等於 5
