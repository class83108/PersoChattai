Feature: Podcast 爬蟲
  作為系統
  我想要定時從 Podcast 網站爬取文章
  以便自動產生學習素材卡片

  Rule: ScraperProtocol

    Scenario: adapter 實作 ScraperProtocol
      Given 一個實作 ScraperProtocol 的 adapter
      Then adapter 具有 source_type 屬性
      And adapter 具有 fetch_article_list 方法
      And adapter 具有 fetch_article_content 方法

  Rule: All Ears English 爬蟲

    Scenario: 成功取得文章列表
      Given AllEarsEnglishScraper 已初始化
      And 模擬目標頁面回傳有效 HTML
      When 呼叫 fetch_article_list
      Then 回傳 ArticleMeta 列表
      And 每個 ArticleMeta 包含 url 和 title

    Scenario: 成功取得文章內容
      Given AllEarsEnglishScraper 已初始化
      And 模擬文章頁面回傳有效 HTML
      When 呼叫 fetch_article_content
      Then 回傳 RawArticle 包含 title content url

    Scenario: 目標頁面無法存取
      Given AllEarsEnglishScraper 已初始化
      And 模擬目標頁面回傳 HTTP 500
      When 呼叫 fetch_article_list
      Then 記錄 warning log
      And 回傳空列表

    Scenario: HTML 結構變更導致解析失敗
      Given AllEarsEnglishScraper 已初始化
      And 模擬目標頁面回傳非預期 HTML 結構
      When 呼叫 fetch_article_list
      Then 記錄 warning log 包含解析失敗位置
      And 回傳空列表

  Rule: BBC 6 Minute English 爬蟲

    Scenario: 成功取得文章列表
      Given BBC6MinuteEnglishScraper 已初始化
      And 模擬目標頁面回傳有效 HTML
      When 呼叫 fetch_article_list
      Then 回傳 ArticleMeta 列表

    Scenario: 成功取得文章內容
      Given BBC6MinuteEnglishScraper 已初始化
      And 模擬文章頁面回傳有效 HTML
      When 呼叫 fetch_article_content
      Then 回傳 RawArticle 包含 title content url

  Rule: 爬蟲輸出契約

    Scenario: ArticleMeta 必須包含 url 和 title
      Given 一個 ArticleMeta 實例
      Then ArticleMeta 具有 url 欄位
      And ArticleMeta 具有 title 欄位

    Scenario: RawArticle 必須包含 title content url
      Given 一個 RawArticle 實例
      Then RawArticle 具有 title 欄位
      And RawArticle 具有 content 欄位
      And RawArticle 具有 url 欄位

  Rule: 爬蟲 Edge Cases

    Scenario: 文章列表為空頁
      Given AllEarsEnglishScraper 已初始化
      And 模擬目標頁面回傳空的文章列表
      When 呼叫 fetch_article_list
      Then 回傳空列表

    Scenario: 文章內容為空白
      Given AllEarsEnglishScraper 已初始化
      And 模擬文章頁面內容區域為空白
      When 呼叫 fetch_article_content
      Then 回傳 RawArticle 的 content 為空字串

  Rule: 爬蟲排程

    Scenario: 排程啟動時註冊 job
      Given ContentScheduler 已初始化
      When 啟動 scheduler
      Then scheduler 包含爬蟲 job

    Scenario: app 關閉時清理 scheduler
      Given ContentScheduler 已啟動
      When 關閉 scheduler
      Then scheduler 正確 shutdown
