## ADDED Requirements

### Requirement: ScraperProtocol 定義
系統 SHALL 定義 `ScraperProtocol`，所有爬蟲 adapter MUST 實作此 Protocol，包含 `source_type` 屬性、`fetch_article_list()` 和 `fetch_article_content()` 方法。

#### Scenario: adapter 實作 Protocol
- **WHEN** 建立新的爬蟲 adapter class
- **THEN** 該 class MUST 提供 `source_type: str`、`async fetch_article_list() -> list[ArticleMeta]`、`async fetch_article_content(url: str) -> RawArticle` 三個成員

### Requirement: All Ears English 爬蟲
系統 SHALL 實作 AllEarsEnglishScraper，從 All Ears English 網站爬取文章列表與內容。

#### Scenario: 成功取得文章列表
- **WHEN** 呼叫 `fetch_article_list()`
- **THEN** 系統從目標頁面解析文章列表，回傳包含 url、title 的 ArticleMeta 列表

#### Scenario: 成功取得文章內容
- **WHEN** 呼叫 `fetch_article_content(url)` 且目標 URL 可存取
- **THEN** 系統回傳包含 title、content（文字內容）、url 的 RawArticle

#### Scenario: 目標頁面無法存取
- **WHEN** 呼叫 `fetch_article_list()` 或 `fetch_article_content()` 且 HTTP 請求失敗
- **THEN** 系統記錄 warning log，回傳空列表或拋出 ScraperError

#### Scenario: HTML 結構變更導致解析失敗
- **WHEN** 目標頁面的 HTML 結構與預期不符
- **THEN** 系統記錄 warning log 包含具體的解析失敗位置，回傳空結果而非 crash

### Requirement: BBC 6 Minute English 爬蟲
系統 SHALL 實作 BBC6MinuteEnglishScraper，從 BBC Learning English 網站爬取文章列表與內容。

#### Scenario: 成功取得文章列表
- **WHEN** 呼叫 `fetch_article_list()`
- **THEN** 系統從目標頁面解析文章列表，回傳包含 url、title 的 ArticleMeta 列表

#### Scenario: 成功取得文章內容
- **WHEN** 呼叫 `fetch_article_content(url)` 且目標 URL 可存取
- **THEN** 系統回傳包含 title、content（文字內容）、url 的 RawArticle

### Requirement: 爬蟲排程
系統 SHALL 使用 APScheduler 定時執行爬蟲任務。

#### Scenario: 排程啟動
- **WHEN** FastAPI app 啟動
- **THEN** APScheduler 註冊爬蟲 job，以設定的 interval 定時執行

#### Scenario: 排程執行爬蟲 job
- **WHEN** 排程觸發爬蟲 job
- **THEN** 系統依序呼叫每個 adapter 的 fetch_article_list → fetch_article_content → content_summarizer pipeline → 建立卡片，已存在的 source_url 自動跳過

#### Scenario: app 關閉時清理 scheduler
- **WHEN** FastAPI app 關閉
- **THEN** APScheduler 正確 shutdown，不殘留背景任務
