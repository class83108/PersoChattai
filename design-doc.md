# PersoChattai — 北極星設計文檔

## 願景

一個 AI 驅動的英文練習 PWA，透過 Role Play 對話、Podcast 內容摘要、能力追蹤形成持續學習迴圈。
部署於 VPS，小圈子使用，API key 由 server 端統一管理。

## 核心學習迴圈

```
素材輸入（Podcast 爬取 / 使用者筆記 PDF / 自由主題 prompt）
       │
       ▼
Claude Agent 生成情境 system instruction
       │
       ▼
Gemini Live API 即時語音 Role Play（含雙向 transcript）
       │
       ▼
Claude Agent 事後分析 transcript → 能力評估
       │
       ▼
累積評估結果 → 調整下次難度 / 推薦素材
       │
       └──→ 回到素材輸入
```

## 架構

```
┌──────────────────────────────────────────────────────────────┐
│  PWA (HTMX + vanilla JS)                                     │
│  ┌─────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │ 素材管理     │  │ Role Play     │  │ 能力報告 / 歷史    │  │
│  │ 卡片瀏覽     │  │ WebRTC 對話   │  │ 成長追蹤           │  │
│  │ 筆記上傳     │  │ 狀態指示器    │  │ API 用量           │  │
│  │ (HTMX)      │  │ (WebRTC + JS) │  │ (HTMX)            │  │
│  └──────┬──────┘  └───────┬───────┘  └─────────┬──────────┘  │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI (VPS)                                                │
│                                                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Content      │  │ Conversation    │  │ Assessment      │  │
│  │ Service      │  │ Service         │  │ Service         │  │
│  │              │  │                 │  │                 │  │
│  │ - 爬蟲排程   │  │ - FastRTC       │  │ - BYOA Agent    │  │
│  │ - PDF 解析   │  │ - Gemini Live   │  │   (Claude)      │  │
│  │ - 卡片生成   │  │ - transcript    │  │ - NLP 量化指標   │  │
│  │ - 輸入驗證   │  │   收集/儲存     │  │ - 難度調整       │  │
│  │   (Claude)   │  │ - 狀態管理      │  │                 │  │
│  └──────┬──────┘  └────────┬────────┘  └────────┬────────┘  │
│         │                  │                     │            │
│         ▼                  ▼                     ▼            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL (VPS)                           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              BYOA Core (Agent 框架)                     │   │
│  │  RealtimeProvider (Gemini Live) │ ClaudeProvider        │   │
│  │  PostgresBackend │ Tool/Skill Registry                  │   │
│  │  UsageMonitor（擴展支援 Gemini 音訊計費）                │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 三大 Service

### 1. Content Service — 素材管理

負責取得、處理、儲存學習素材。

**素材來源（三種管道）：**

| 管道 | 輸入 | 處理 | 產出 |
|------|------|------|------|
| Podcast 爬取 | All Ears English / BBC 6 Minute English | 爬取文字內容 → Claude 摘要 | 摘要卡片（可拆多張） |
| 使用者筆記 | PDF 上傳 | 驗證 + 截斷 → Claude 提取重點 | 摘要卡片（可拆多張） |
| 自由主題 | 使用者輸入 prompt | Claude 展開主題 | 情境 prompt |

**爬蟲設計：**
- 排程：APScheduler（FastAPI 生態內）
- 目標網站各自一個 Scraper adapter（Protocol-based）
- 來源：
  - All Ears English：`/category/business-english/` 分頁列表 → 個別文章頁抓內容
  - BBC 6 Minute English：`/features/6-minute-english_2026/` 系列頁面

**輸入驗證與使用者回饋：**

| 檢查項目 | 限制 | 使用者看到的訊息 |
|---------|------|----------------|
| PDF 檔案大小 | 最大 10MB | 「檔案過大，請上傳 10MB 以下的 PDF」 |
| PDF 文字內容長度 | 最大 5000 字 | 「內容過長，將自動擷取前 5000 字進行摘要」 |
| PDF 解析失敗 | 無法提取文字 | 「無法讀取此 PDF，請確認檔案包含文字內容（非純圖片）」 |
| 自由主題 prompt | 最大 500 字 | 「主題描述過長，請精簡至 500 字以內」 |
| 爬蟲失敗 | 來源網站無回應 | 管理員通知，不影響使用者 |

**卡片結構：**
- 來源類型 / 來源 URL / 標題 / 日期
- 原文摘要（3-5 句）
- 關鍵詞彙 + 解釋
- 對話片段（如有）
- 難度標籤（CEFR 等級）
- 可組合 tag

### 2. Conversation Service — 對話管理

負責 Role Play 語音對話的全生命週期。

**對話流程：**

```
1. 使用者選擇素材（卡片 / 筆記 / 自由主題）
2. Claude Agent 根據素材 + 使用者能力等級 → 生成 Gemini system instruction
3. 建立 Gemini Live API session
   - response_modalities: ["AUDIO"]
   - input_audio_transcription: {}
   - output_audio_transcription: {}
   - system_instruction: Claude 生成的情境 prompt
4. FastRTC 建立 WebRTC 連線
5. 使用者與 Gemini 即時語音對話
6. 同時收集 transcript 事件（input_transcription + output_transcription）
7. 對話結束 → 儲存完整 transcript 至 PostgreSQL
8. 觸發事後評估 pipeline
```

**對話狀態管理與使用者回饋：**

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│ 準備中   │───→│ 連線中    │───→│ 對話中   │───→│ 評估中   │───→│ 完成     │
│preparing│    │connecting│    │  active  │    │assessing │    │completed │
└────────���┘    └──────────┘    └─────────┘    └──────────┘    └──────────┘
                    │               │
                    ▼               ▼
               ┌──────────┐   ┌──────────┐
               │ 連線失敗  │   │ 已取消    │
               │  failed   │   │cancelled │
               └──────────┘   └──────────┘
```

| 狀態 | 使用者看到的 UI | 說明 |
|------|---------------|------|
| preparing | 「正在準備對話情境...」+ loading | Claude 生成 system instruction |
| connecting | 「正在建立語音連線...」+ loading | WebRTC + Gemini session 建立 |
| active | 計時器 + 音量指示器 + 「結束對話」按鈕 | 對話進行中 |
| assessing | 「正在分析對話內容...」+ loading | NLP + Claude 評估 |
| completed | 評估結果卡片 | 顯示本次評估 |
| failed | 「連線失敗，請重試」+ 重試按鈕 | 錯誤處理 |
| cancelled | 回到素材選擇頁 | 使用者主動取消 |

**對話 Reset 觸發條件：**

| 觸發條件 | 行為 | 使用者提示 |
|---------|------|----------|
| 使用者按「結束對話」 | 儲存 transcript → 觸發評估 | 進入 assessing 狀態 |
| 時間上限（15 分鐘） | 提前 2 分鐘警告，到時自動結束 | 「對話即將結束，剩餘 2 分鐘」 |
| 靜默超時（2 分鐘） | 自動結束 | 「偵測到長時間靜默，對話已結束」 |
| 連線斷開 | 儲存已收集的 transcript | 「連線中斷，已儲存目前的對話內容」 |

**FastRTC 整合：**
- GeminiHandler（AsyncStreamHandler 子類別）
- 處理音訊雙向流 + transcript 收集
- mount 至 FastAPI app

### 3. Assessment Service — 能力評估

負責分析對話 transcript、追蹤能力成長。

**評估時機：** 每次對話結束後自動觸發（事後分析）。
**評估範圍：** Role Play 對話 + 自由對話，所有對話類型皆追蹤。
**初始等級：** 不設入門測試，第一次使用中等難度（B1-B2），事後評估建立 baseline。

#### 評估框架：3 維度 × 雙層評分

參考 IELTS Speaking Band Descriptors，去除 Pronunciation（不評發音），保留三個維度：

| 維度 | 質性評估（Claude 判斷） | 量化指標（NLP 計算） |
|------|------------------------|---------------------|
| **Lexical Resource** | 詞彙精準度、idiomatic expressions 使用、paraphrase 能力 | MTLD、VOCD-D、K1/K2/AWL 分佈、新詞出現率 |
| **Fluency & Coherence** | 想法連貫度、discourse markers 使用、自我修正頻率 | 平均句長、連接詞比例、自我修正次數 |
| **Grammatical Range & Accuracy** | 句型多樣性、語法錯誤嚴重度 | 從句比例、時態多樣性、語法錯誤率 |

#### 量化指標

**Lexical Resource（核心追蹤維度）：**

| 指標 | 說明 | 用途 |
|------|------|------|
| MTLD | Measure of Textual Lexical Diversity，不受文本長度影響 | 詞彙多樣性主指標 |
| VOCD-D | 隨機取樣 TTR 平均值，100-500 字最可靠 | 詞彙多樣性輔助指標 |
| K1/K2/AWL 分佈 | 用字在常見 1000/2000 字及學術詞彙中的佔比 | 詞彙等級分佈 |
| 新詞出現率 | 跨 session 比對：本次新使用的詞彙 | 成長追蹤核心 |

**Fluency & Coherence：**

| 指標 | 說明 |
|------|------|
| 平均句長 | tokens per sentence |
| 連接詞比例 | discourse markers / total sentences |
| 自我修正次數 | 偵測 "I mean", "sorry", "no wait" 等 pattern |

**Grammatical Range & Accuracy：**

| 指標 | 說明 |
|------|------|
| 從句比例 | subordinate clauses / total sentences |
| 時態多樣性 | unique tense forms used |
| 語法錯誤率 | NLP grammar checker 輔助 |

#### CEFR 等級映射（六級制）

| CEFR | IELTS 對應 | MTLD 參考 | 詞彙特徵 |
|------|-----------|----------|---------|
| A1 | 1-2 | < 25 | 極基礎詞彙，僅能應對最簡單互動 |
| A2 | 3-4 | 25-40 | 基本詞彙處理熟悉話題 |
| B1 | 4-5 | 40-60 | 足夠詞彙量但靈活度有限 |
| B2 | 5-6 | 60-80 | 能展開討論，偶爾用錯不影響理解 |
| C1 | 7-8 | 80-100 | 靈活使用 uncommon/idiomatic 表達 |
| C2 | 8-9 | > 100 | 完全靈活精準，持續使用道地表達 |

MTLD 參考範圍為初始值，累積足夠使用者數據後校正。

#### 雙層評估 Pipeline

```
對話結束
   │
   ▼
NLP Pipeline（自動計算，不經 Agent）
   - MTLD / VOCD-D
   - K1/K2/AWL 分佈
   - 句長 / 從句比例 / 時態多樣性
   - 自我修正偵測
   - 新詞出現率（vs 使用者歷史詞彙庫）
   → 產出 metrics JSON
   │
   ▼
Claude Agent（質性分析，transcript_evaluator skill）
   - 輸入：transcript + metrics + 情境 prompt + user history
   - 判斷：CEFR 等級、各維度強弱、具體改善建議
   - 輸出：結構化評估 JSON（含 new_words 列表）
   │
   ▼
Service 層後處理（自動，不經 Agent）
   - 寫入 assessments 表
   - 更新 user_vocabulary 表（根據 new_words）
   - 檢查是否需要產生 level_snapshot（每 N 次對話）
   - 更新 users.current_level
```

#### 歷史資料分層策略

每次對話產生獨立評估（保留變化軌跡），Claude 分析時帶入摘要過的歷史：

```
get_user_history(user_id) 回傳：
   ├── 最新 level_snapshot → 整體能力概況
   ├── 最近 5 次 assessments → 近期表現細節
   └── user_vocabulary 統計 → 詞彙庫大小 + 最近新增詞
```

**level_snapshot 產生時機：** 每 5 次對話自動聚合（APScheduler 或對話計數觸發）。

## BYOA Core 擴展

### Provider

```
LLMProvider (既有 Protocol，request-response)
└── AnthropicProvider (既有) — 情境生成、評估、摘要

RealtimeProvider (新增 Protocol，串流語音)
└── GeminiRealtimeProvider (新增) — Live API 雙向音訊 + transcript
```

### SessionBackend

```
SessionBackend (既有 Protocol)
├── MemoryBackend (既有)
├── SQLiteBackend (既有)
└── PostgresBackend (新增)
```

### UsageMonitor 擴展

繼承既有 BYOA UsageMonitor，擴展支援 Gemini Live API 計費模式：

| 現有 | 擴展 |
|------|------|
| MODEL_PRICING 有 Claude + OpenAI | 加入 Gemini 定價（Live API 按音訊秒數計費） |
| UsageRecord 追蹤 token | 加 audio_duration_sec 欄位 |
| 記憶體內 records | 加 PostgreSQL 持久化（重啟不丟失） |
| get_summary() 回傳 JSON | 前端 HTMX 頁面顯示用量 |

### Tools（3 個）

| Tool | 所屬 Service | 功能 |
|------|-------------|------|
| `query_cards` | Content | 查詢素材卡片（依 tag / 難度 / 來源 / 關鍵字篩選） |
| `get_user_history` | Assessment | 取最新 snapshot + 最近 5 次評估 + 詞彙統計 |
| `create_card` | Content | 建立摘要卡片（一篇素材可拆多張） |

### Skills（3 個）

| Skill | 觸發時機 | 輸入 | 輸出 |
|------|---------|------|------|
| `content_summarizer` | 爬取完成 / PDF 上傳後 | 原始文字內容 | 呼叫 create_card 建立卡片 |
| `scenario_designer` | 使用者選素材開始對話 | 卡片內容 + user history | system instruction JSON |
| `transcript_evaluator` | 對話結束後 | transcript + NLP metrics + user history | 結構化評估 JSON（含 new_words） |

### 自動化 Pipeline（Service 層，不經 Agent）

| 任務 | 觸發方式 |
|------|---------|
| Podcast 爬取 | APScheduler 定時 |
| NLP metrics 計算 | 對話結束後自動 |
| user_vocabulary 更新 | Claude 評估完成後自動（根據輸出的 new_words） |
| level_snapshot 聚合 | 每 5 次對話自動 |
| UsageMonitor 持久化 | 每次 API 呼叫後自動 |

## DB Schema

```sql
users (
  id uuid PK,
  display_name text,
  current_level text,       -- CEFR A1-C2，初始 null
  created_at timestamptz
)

cards (
  id uuid PK,
  source_type text,          -- 'podcast_allearsenglish' | 'podcast_bbc' | 'user_pdf' | 'user_prompt'
  source_url text,
  title text,
  summary text,
  keywords jsonb,            -- [{word, definition, example}]
  dialogue_snippets jsonb,
  difficulty_level text,     -- CEFR
  tags text[],
  created_at timestamptz
)

conversations (
  id uuid PK,
  user_id uuid FK,
  conversation_type text,    -- 'roleplay' | 'free_chat'
  source_type text,          -- 'card' | 'pdf' | 'free_topic'
  source_ref text,           -- card_id / pdf filename / topic prompt
  system_instruction text,
  started_at timestamptz,
  ended_at timestamptz,
  transcript jsonb,          -- [{role, text, timestamp}]
  status text                -- 'preparing' | 'connecting' | 'active' | 'assessing' | 'completed' | 'failed' | 'cancelled'
)

assessments (
  id uuid PK,
  conversation_id uuid FK,
  user_id uuid FK,
  -- 量化指標
  mtld float,
  vocd_d float,
  k1_ratio float,
  k2_ratio float,
  awl_ratio float,
  new_words_count int,
  new_words text[],
  avg_sentence_length float,
  conjunction_ratio float,
  self_correction_count int,
  subordinate_clause_ratio float,
  tense_diversity int,
  grammar_error_rate float,
  -- 質性分析
  cefr_level text,           -- A1-C2
  lexical_assessment text,
  fluency_assessment text,
  grammar_assessment text,
  suggestions text[],
  raw_analysis jsonb,
  created_at timestamptz
)

user_vocabulary (
  id uuid PK,
  user_id uuid FK,
  word text,
  first_seen_at timestamptz,
  first_seen_conversation_id uuid FK,
  occurrence_count int,
  UNIQUE(user_id, word)
)

user_level_snapshots (
  id uuid PK,
  user_id uuid FK,
  snapshot_date date,
  cefr_level text,
  avg_mtld float,
  avg_vocd_d float,
  vocabulary_size int,
  strengths text[],
  weaknesses text[],
  conversation_count int,    -- 截至此快照的總對話數
  created_at timestamptz
)

api_usage (
  id uuid PK,
  usage_type text,             -- 'token' | 'audio'
  model text,
  input_tokens int,
  output_tokens int,
  cache_creation_input_tokens int,
  cache_read_input_tokens int,
  audio_duration_sec float,
  direction text,              -- 'input' | 'output'（audio only）
  cost_usd float,
  created_at timestamptz
)
```

## 技術選型

| 層級 | 技術 | 理由 |
|------|------|------|
| Agent 框架 | BYOA Core | Protocol-based 可擴展、session/tool 管理、內建 UsageMonitor |
| 語音對話 | Gemini Live API | 低延遲、內建雙向 transcript。模型可配置（預設 gemini-2.0-flash） |
| 思考/評估 | Claude API (via BYOA) | 情境設計、能力評估、內容摘要。模型可配置（預設 claude-sonnet-4-20250514） |
| 後端 | FastAPI | async、與 FastRTC 整合 |
| 即時音訊 | FastRTC | WebRTC 封裝、Python 原生、mount FastAPI |
| 前端 | HTMX + vanilla JS | server-side rendering、輕量 PWA |
| 資料庫 | PostgreSQL (VPS) | 自建、免費、直連 |
| 爬蟲排程 | APScheduler | FastAPI 生態內 |
| NLP 指標 | lexical_diversity + spaCy | MTLD/VOCD-D 計算、語法分析 |
| 品質 | ruff + pyright + pytest-bdd | 既有工作流 |
| 部署 | VPS | 單機部署、.env 管 API key |
| 模型配置 | Settings + /api/settings 端點 | Claude / Gemini 模型可從前端切換，定價表隨模型連動 |

## 使用者識別

小圈子使用，不做完整認證系統，以暱稱識別使用者。

**流程：**

```
首次進站
   │
   ▼
彈出 modal → 輸入暱稱（唯一）
   │
   ▼
POST /api/users → 建立 user row（UUID + display_name）
   │
   ▼
存 localStorage（persochattai_user_id + persochattai_display_name）
   │
   ▼
後續進站 → localStorage 有值就直接用，navbar 顯示暱稱
```

**規則：**

| 項目 | 規則 |
|------|------|
| 暱稱唯一性 | 唯一，重複回傳 409 |
| 暱稱格式 | 1-20 字，不限字元類型 |
| 認證機制 | 無密碼，純暱稱識別 |
| 切換使用者 | navbar「換人」→ 清除 localStorage → 重新輸入暱稱 |
| 已存在暱稱 | 視為同一人，回傳該 user 的 UUID |

**解決的問題：**
- `conversations.user_id` FK 約束需要 `users` 表有對應 row
- 前端 `getUserId()` 產生的 UUID 未寫入 DB
- 報告、評估歷史需要穩定的 user_id 關聯

## MVP 範圍

1. **Podcast 爬取 + 卡片生成** — All Ears English + BBC 6 Minute English
2. **Role Play 對話** — 三種素材來源 → Gemini Live 語音對話 → transcript 收集
3. **事後能力評估** — NLP 量化 + Claude 質性分析 → CEFR 六級制 → 儲存
4. **使用者狀態回饋** — 對話狀態指示、輸入驗證提示、API 用量顯示

## 未來功能（P1+）

- 即時自由對話（無情境，純聊天，同樣追蹤評估）
- 能力追蹤儀表板（跨 session 成長曲線）
- 自動難度調整（根據歷史 CEFR 等級調整 system instruction）
- 發音評估（Azure Pronunciation Assessment，音訊 buffer 預留）
- Podcast 腳本生成 + GCP TTS（筆記 → podcast 音檔）
- BYOK 支援（使用者自帶 API key）
- 多使用者認證
