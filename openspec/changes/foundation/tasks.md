## 1. 環境配置

- [x] 1.1 建立 .env.example（DB_URL, ANTHROPIC_API_KEY, GEMINI_API_KEY, DEBUG）
- [x] 1.2 建立 config.py — Settings dataclass + .env 讀取 + 缺少變數報錯

## 2. DB Schema

- [x] 2.1 建立 migrations/001_init.sql — 所有 6 張表的 CREATE TABLE IF NOT EXISTS
- [x] 2.2 建立 db.py — asyncpg connection pool（init_pool / close_pool）
- [x] 2.3 建立 models.py — 所有資料表對應的 Pydantic models

## 3. FastAPI App

- [x] 3.1 建立 app.py — create_app() factory + lifespan（DB pool lifecycle）
- [x] 3.2 建立 health check endpoint（GET /health）
- [x] 3.3 建立 content/router.py — 空 router 骨架，掛載至 /api/content
- [x] 3.4 建立 conversation/router.py — 空 router 骨架，掛載至 /api/conversation
- [x] 3.5 建立 assessment/router.py — 空 router 骨架，掛載至 /api/assessment

## 4. BYOA Core 整合

- [x] 4.1 建立 agent_factory.py — 共用 AnthropicProvider + UsageMonitor 初始化
- [x] 4.2 實作 create_content_agent() factory
- [x] 4.3 實作 create_conversation_agent() factory
- [x] 4.4 實作 create_assessment_agent() factory
- [x] 4.5 建立 GET /api/usage endpoint（回傳 UsageMonitor.get_summary()）

## 5. 驗證

- [ ] 5.1 撰寫 .feature 檔（環境配置、DB 連線、app 啟動、router 掛載）
- [ ] 5.2 撰寫 pytest-bdd step definitions
- [ ] 5.3 確認 ruff check + ruff format + pyright 全部通過
