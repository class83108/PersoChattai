## ADDED Requirements

### Requirement: PDF 上傳
系統 SHALL 提供 `POST /api/content/upload-pdf` endpoint，接受 PDF 檔案上傳並解析文字內容。

#### Scenario: 成功上傳並解析 PDF
- **WHEN** 使用者上傳有效的 PDF 檔案（< 10MB，含文字內容）
- **THEN** 系統解析文字 → 呼叫 content_summarizer pipeline → 回傳產出的卡片列表

#### Scenario: 檔案超過大小限制
- **WHEN** 使用者上傳超過 10MB 的 PDF 檔案
- **THEN** 系統回傳 HTTP 413，訊息為「檔案過大，請上傳 10MB 以下的 PDF」

#### Scenario: 文字內容超過長度限制
- **WHEN** PDF 解析出的文字超過 5000 字
- **THEN** 系統自動截斷至 5000 字（句子邊界），繼續處理，回應中包含截斷提示

#### Scenario: PDF 無法解析文字
- **WHEN** 上傳的 PDF 無法提取文字（純圖片 PDF）
- **THEN** 系統回傳 HTTP 422，訊息為「無法讀取此 PDF，請確認檔案包含文字內容（非純圖片）」

### Requirement: 自由主題
系統 SHALL 提供 `POST /api/content/free-topic` endpoint，接受使用者輸入的主題描述。

#### Scenario: 成功建立自由主題卡片
- **WHEN** 使用者提交有效的主題描述（1-500 字）
- **THEN** 系統呼叫 content_summarizer pipeline → 回傳產出的卡片

#### Scenario: 主題描述過長
- **WHEN** 使用者提交超過 500 字的主題描述
- **THEN** 系統回傳 HTTP 422，訊息為「主題描述過長，請精簡至 500 字以內」

#### Scenario: 主題描述為空
- **WHEN** 使用者提交空白的主題描述
- **THEN** 系統回傳 HTTP 422，驗證錯誤訊息
