## Context

Conversation Service 已能收集完整 transcript（`[{role, text, timestamp}]`），但對話結束後只標記 `completed` 狀態，沒有實際分析。Assessment Service 需要：
1. 接收 transcript，跑 NLP 量化指標
2. 將 transcript + metrics 送 Claude Agent 做質性分析
3. 儲存評估結果、更新使用者詞彙庫、定期聚合 level snapshot

現有 `assessment/` 只有空殼 router（health endpoint）。

## Goals / Non-Goals

**Goals:**
- 實作雙層評估 pipeline（NLP → Claude → 後處理）
- 評估結果可查詢（單次評估、歷史列表、詞彙統計）
- 使用者能力等級可追蹤（CEFR A1-C2）
- 提供 `get_user_history` tool 給 BYOA Agent 使用

**Non-Goals:**
- 發音評估（未來 P1+ 用 Azure Pronunciation Assessment）
- 即時評估（只做事後分析）
- 前端 UI（本次只做 API 層）
- 自動難度調整邏輯（未來功能，本次只儲存等級）

## Decisions

### 1. NLP Pipeline 作為獨立模組 `nlp.py`

NLP 指標計算是純函式、無 IO 依賴，獨立成 `nlp.py` 模組，不經 Agent。

**替代方案：** 放在 service.py 內。
**選擇理由：** 職責分離——NLP 是數學計算，service 是流程編排。獨立模組方便單元測試、未來替換 NLP 工具。

### 2. spaCy 做語法分析，lexical-diversity 做詞彙多樣性

- `lexical-diversity`：提供 MTLD、VOCD-D，輕量 Python library
- `spaCy` + `en_core_web_sm`：POS tagging、dependency parsing、句子分割，用於從句比例、時態多樣性、語法分析

**替代方案：** NLTK、stanza。
**選擇理由：** spaCy 速度快、API 乾淨、模型小（`en_core_web_sm` ~12MB）。lexical-diversity 專注 MTLD/VOCD-D 計算，比自己實作可靠。

### 3. K1/K2/AWL 用內建詞頻表

將 BNC/COCA K1（前 1000 常用字）、K2（1001-2000）、AWL（學術詞彙表）作為 Python set 內建於 `nlp.py`。

**替代方案：** 外部 CSV/JSON 檔。
**選擇理由：** 這些詞表是固定的語言學標準，不會變動。內建避免 IO、部署簡單。詞表大小約 2000+570 個字，記憶體可忽略。

### 4. 評估觸發方式：Conversation Service 呼叫 Assessment Service

對話結束時，`ConversationManager.end_conversation()` 直接呼叫 `AssessmentService.evaluate()`。不用事件系統或訊息佇列。

**替代方案：** Event bus、background task queue。
**選擇理由：** 目前單機部署、使用者量小，直接呼叫最簡單。評估是非同步的（`async`），不阻塞回應。未來需要解耦時再抽出。

### 5. user_vocabulary 更新依賴 Claude 輸出的 new_words

Claude Agent 的 transcript_evaluator skill 會在評估結果中輸出 `new_words` 列表。Service 層根據此列表更新 `user_vocabulary` 表（INSERT ON CONFLICT 累加 occurrence_count）。

**替代方案：** NLP 自動偵測新詞。
**選擇理由：** Claude 能理解上下文判斷「有意義的新詞」（排除口語填充詞、重複錯誤等），比純 NLP 比對更準確。

### 6. level_snapshot 由對話計數觸發

每次評估後檢查該使用者的評估總數，若為 5 的倍數則產生 snapshot。不用 APScheduler。

**替代方案：** 定時排程聚合。
**選擇理由：** 按對話次數觸發更精確（使用者可能一天對話 5 次或一週 1 次），避免空轉排程。

## Risks / Trade-offs

- **spaCy 模型下載**：首次部署需 `python -m spacy download en_core_web_sm`。→ 寫入 pyproject.toml post-install 或 Dockerfile。
- **Claude API 延遲**：質性分析需要一次 Claude API call，可能 3-10 秒。→ 使用者在 `assessing` 狀態等待，UI 顯示 loading。不影響對話體驗（已結束）。
- **NLP 指標對短文本不穩定**：MTLD/VOCD-D 在文本太短（<50 tokens）時不可靠。→ NLP 模組對短文本回傳 null/None，Claude 評估時標記為「樣本不足」。
- **詞頻表覆蓋率**：內建 K1/K2/AWL 可能遺漏某些變形。→ 使用 spaCy lemmatization 後再比對，提高覆蓋率。
