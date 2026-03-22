## 1. DB 與 Repository

- [x] 1.1 新增 `display_name` UNIQUE 約束（Alembic migration）
- [x] 1.2 建立 `UserRepository`（get_by_id, get_by_display_name, create）
- [x] 1.3 建立 `UserRepositoryWrapper`（session-per-call 模式）

## 2. API 端點

- [x] 2.1 建立 `POST /api/users` endpoint（建立或回傳既有使用者）
- [x] 2.2 建立 `GET /api/users/{user_id}` endpoint（驗證使用者存在）
- [x] 2.3 在 `app.py` lifespan 初始化 UserRepositoryWrapper 並掛載 user router

## 3. 前端 — 暱稱 Modal

- [x] 3.1 建立 `nickname_modal.html` partial（全頁 modal + 暱稱 input + 提交按鈕）
- [x] 3.2 在 `base.html` 引入 modal partial
- [x] 3.3 改寫 `app.js` 的 `getUserId()` 流程（API 驗證 + modal 觸發）

## 4. 前端 — Navbar 整合

- [x] 4.1 在 navbar 顯示暱稱 + 「換人」按鈕
- [x] 4.2 實作換人功能（清除 localStorage → 顯示 modal）

## 5. Conversation API 整合

- [x] 5.1 在 `POST /api/conversation/start` 加入 user_id 存在性驗證
