## ADDED Requirements

### Requirement: 批次 URL 去重
系統 SHALL 在 fetch_article_content 之前，批次查詢 DB 過濾已存在的 source_url，避免不必要的網路請求與 LLM 呼叫。

#### Scenario: 文章列表中有已爬過的 URL
- **WHEN** fetch_article_list 回傳 10 篇文章，其中 7 篇的 source_url 已存在於 DB
- **THEN** 系統只對剩餘 3 篇呼叫 fetch_article_content 與 summarize，7 篇標記為 skipped

#### Scenario: 文章列表全部是新的
- **WHEN** fetch_article_list 回傳的所有 source_url 都不存在於 DB
- **THEN** 系統對所有文章執行完整的 fetch → summarize → insert 流程

#### Scenario: 文章列表全部已存在
- **WHEN** fetch_article_list 回傳的所有 source_url 都已存在於 DB
- **THEN** 系統跳過所有文章，不呼叫任何 fetch_article_content 或 summarize

### Requirement: 批次 URL 存在檢查
CardRepository SHALL 提供 `filter_existing_urls(urls: list[str]) -> set[str]` 方法，一次查詢回傳已存在的 URL 集合。

#### Scenario: 查詢多個 URL 的存在性
- **WHEN** 呼叫 `filter_existing_urls(["url1", "url2", "url3"])` 且 url1、url3 已存在
- **THEN** 回傳 `{"url1", "url3"}`

#### Scenario: 空列表查詢
- **WHEN** 呼叫 `filter_existing_urls([])`
- **THEN** 回傳空 set，不執行 DB 查詢
