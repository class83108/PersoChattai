## Why

前端 `getUserId()` 會在 localStorage 生成 UUID，但從未寫入 DB 的 `users` 表。所有帶 `user_id` FK 的操作（建立對話、查詢評估歷史）都會 500。需要一個最簡使用者識別流程，讓 user row 在 DB 中存在。

## What Changes

- 新增使用者建立 API：`POST /api/users`（暱稱唯一，回傳 UUID）
- 新增使用者查詢 API：`GET /api/users/{user_id}`
- 前端首次進站彈出暱稱輸入 modal，建立 user 後存 localStorage
- 後續進站自動帶入，navbar 顯示暱稱 + 「換人」功能
- 改寫 `getUserId()` 流程：從「本地生成 UUID」改為「從 API 取得 UUID」

## Capabilities

### New Capabilities
- `user-identity`: 使用者建立與識別流程（API + 前端 modal + localStorage 管理）

### Modified Capabilities
- `app-bootstrap`: lifespan 中需確保 user 相關 repository 可用
- `conversation-api`: conversation start 時驗證 user_id 存在於 DB

## Impact

- **新增檔案**: `src/persochattai/user/router.py`, `src/persochattai/user/repository.py`, `templates/partials/nickname_modal.html`
- **修改檔案**: `static/js/app.js`（getUserId 流程）, `templates/base.html`（navbar 暱稱 + modal）, `src/persochattai/app.py`（掛載 user router + repo）
- **DB**: 使用既有 `users` 表，新增 `display_name` UNIQUE 約束
- **API**: 新增 `/api/users` 端點
