## Context

能力報告頁面串接 Assessment Service 和 Usage API。後端已提供：
- `GET /api/assessment/user/{user_id}/progress` — 進度（含 CEFR 等級、維度分數）
- `GET /api/assessment/user/{user_id}/history` — 評估歷史列表
- `GET /api/assessment/user/{user_id}/vocabulary` — 詞彙統計
- `GET /api/assessment/{id}` — 單筆評估詳情
- `GET /api/usage` — API 用量摘要

## Goals / Non-Goals

**Goals:**
- 概覽區：CEFR 等級 badge + 三維度 progress bar
- 評估歷史：HTMX 列表 + 展開詳情
- 詞彙統計：total words、new words rate
- API 用量：token 使用量、cost

**Non-Goals:**
- 不做圖表（Chart.js 等），先用文字/進度條
- 不做 PDF 匯出
- 不做跨使用者比較

## Decisions

### 1. HTMX Partial 模式（同素材管理）

Frontend router 新增 partial 端點：
- `GET /report/partials/overview` — 概覽 fragment
- `GET /report/partials/history` — 歷史列表 fragment
- `GET /report/partials/vocabulary` — 詞彙統計 fragment
- `GET /report/partials/usage` — 用量 fragment

所有 partial 內部代理 JSON API → 渲染 HTML fragment。

### 2. 三維度視覺化：DaisyUI progress bar

三維度（Lexical / Fluency / Grammar）用 `progress` 元件顯示，搭配分數文字。CEFR 等級用 `badge badge-lg` 突出顯示。

### 3. 頁面結構

```
┌─────────────────────────────────────────┐
│ 能力報告                                 │
├──────────────────┬──────────────────────┤
│ CEFR Badge       │  詞彙統計             │
│ 三維度 progress   │  API 用量             │
├──────────────────┴──────────────────────┤
│ 評估歷史列表                              │
└─────────────────────────────────────────┘
```

## Risks / Trade-offs

- **無圖表** → 成長趨勢不夠直觀。Mitigation：後續可加 Chart.js，目前 progress bar + 數值足夠小圈子使用。
- **user_id 同 roleplay** → 使用 localStorage UUID。Mitigation：認證系統加入後統一替換。
