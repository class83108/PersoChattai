## 1. Partial Templates

- [x] 1.1 建立 `templates/partials/ability_overview.html`（CEFR badge + 三維度 progress）
- [x] 1.2 建立 `templates/partials/assessment_history.html`（歷史列表）
- [x] 1.3 建立 `templates/partials/assessment_item.html`（單筆評估，可展開）
- [x] 1.4 建立 `templates/partials/vocabulary_stats.html`（詞彙統計）
- [x] 1.5 建立 `templates/partials/usage_summary.html`（API 用量）

## 2. Frontend Router — Partial 端點

- [x] 2.1 新增 `GET /report/partials/overview` 端點
- [x] 2.2 新增 `GET /report/partials/history` 端點
- [x] 2.3 新增 `GET /report/partials/vocabulary` 端點
- [x] 2.4 新增 `GET /report/partials/usage` 端點

## 3. 報告頁面重構

- [x] 3.1 重寫 `templates/pages/report.html`：概覽區 + 統計卡片 + 歷史列表
- [x] 3.2 所有區塊使用 `hx-get` + `hx-trigger="load"` 動態載入
