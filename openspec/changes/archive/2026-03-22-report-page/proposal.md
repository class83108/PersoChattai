## Why

能力報告頁面（`/report`）目前只是 placeholder。使用者需要查看英文能力成長追蹤、歷史評估、詞彙統計、API 用量。後端已有 Assessment API 和 Usage API。

## What Changes

- 能力概覽：CEFR 等級、三維度分數（Lexical / Fluency / Grammar）
- 評估歷史列表（HTMX 動態載入）
- 單筆評估展開查看詳情
- 詞彙統計卡片
- API 用量摘要
- 成長趨勢（簡單的文字指標，不做圖表）

## Capabilities

### New Capabilities
- `ability-overview`: 能力概覽區塊，顯示 CEFR 等級和三維度分數
- `assessment-history`: 評估歷史列表，展開查看詳情
- `usage-summary`: API 用量與詞彙統計摘要

### Modified Capabilities
（無）

## Impact

- **修改檔案**: `templates/pages/report.html`
- **新增檔案**: `templates/partials/assessment_*.html` 系列 partial templates
- **修改路由**: frontend router 新增 report 相關 partial 端點
- **依賴**: `/api/assessment/*` + `/api/usage` API endpoints
