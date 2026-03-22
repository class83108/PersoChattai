## Context

目前 `getUserId()` 在前端用 `crypto.randomUUID()` 產生 UUID 存 localStorage，但 DB `users` 表是空的。所有需要 `user_id` FK 的操作（conversations、assessments）都會失敗。

既有 `users` 表已有 `id` (UUID PK)、`display_name` (Text NOT NULL)、`current_level`、`created_at` 欄位，schema 不需要改動，只需新增 `display_name` UNIQUE 約束。

## Goals / Non-Goals

**Goals:**
- 讓每個使用者在 DB 有對應的 user row
- 暱稱唯一，輸入重複暱稱時視為「登入」該使用者
- 最小改動量，不引入認證框架

**Non-Goals:**
- 密碼 / OAuth / JWT 認證
- 使用者管理後台
- 多裝置同步（localStorage 為主，換裝置需重新輸入暱稱）

## Decisions

### D1: 暱稱重複時的行為 — 回傳既有 user 而非 409

**選擇**: `POST /api/users` 收到已存在暱稱時，回傳該 user 的 UUID（200），而非 409 Conflict。

**理由**: 沒有密碼保護，409 會讓使用者卡住（無法「登入」自己之前用過的暱稱）。等同於「暱稱即身份」，輸入暱稱 = 取得該使用者的所有歷史資料。

**風險**: 任何人都能輸入別人的暱稱存取其資料。可接受 — 小圈子使用，未來加認證時再收緊。

### D2: 前端流程 — 阻斷式 modal

**選擇**: 首次進站（localStorage 無 user_id）時顯示全頁 modal，輸入暱稱後才能操作。

**理由**: 確保所有頁面都有合法 user_id。比起在各功能頁面各自檢查，統一在 `base.html` 處理最簡單。

### D3: Repository 層 — 複用 session_wrapper 模式

**選擇**: 新增 `UserRepository` + `UserRepositoryWrapper`，遵循既有的 session-per-call 模式。

**理由**: 與 `CardRepositoryWrapper`、`AssessmentRepositoryWrapper` 等一致，不引入新模式。

### D4: API 設計 — 單一端點處理建立與查詢

| 端點 | 用途 |
|------|------|
| `POST /api/users` | 建立新使用者 or 回傳既有使用者（by display_name） |
| `GET /api/users/{user_id}` | 驗證 user_id 是否存在（前端啟動時呼叫） |

### D5: 前端 getUserId() 改造

```
頁面載入
  │
  ├─ localStorage 有 user_id?
  │   ├─ YES → GET /api/users/{user_id} 驗證
  │   │         ├─ 200 → 正常使用，navbar 顯示暱稱
  │   │         └─ 404 → 清除 localStorage → 顯示 modal
  │   └─ NO → 顯示 modal
  │
  modal 提交暱稱
  │
  └─ POST /api/users {display_name}
       ├─ 200/201 → 存 user_id + display_name 到 localStorage → 關閉 modal
       └─ 422 → 顯示驗證錯誤
```

## Risks / Trade-offs

- **[無認證安全風險]** → 可接受：小圈子使用，北極星文件已標示「多使用者認證」為 P1+ 功能
- **[localStorage 清除導致失聯]** → 使用者重新輸入暱稱即可恢復（D1 決策）
- **[暱稱碰撞]** → UNIQUE 約束 + 前端即時提示「此暱稱已被使用，是否以此身份繼續？」
