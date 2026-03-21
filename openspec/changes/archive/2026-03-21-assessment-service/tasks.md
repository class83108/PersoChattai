## 1. Schemas + Repository

- [x] 1.1 建立 assessment/schemas.py — NlpMetrics、AssessmentRepositoryProtocol、VocabularyRepositoryProtocol、SnapshotRepositoryProtocol、AssessmentAgentProtocol、AssessmentServiceProtocol
- [x] 1.2 建立 assessment/repository.py — AssessmentRepository（create、get_by_id、list_by_user、count_by_user）
- [x] 1.3 建立 assessment/vocabulary_repository.py — UserVocabularyRepository（upsert_words、get_vocabulary_stats）
- [x] 1.4 建立 assessment/snapshot_repository.py — LevelSnapshotRepository（create_snapshot、get_latest）

## 2. NLP Pipeline

- [x] 2.1 建立 assessment/nlp.py — NlpAnalyzer 骨架（analyze 方法回傳 NlpMetrics）
- [x] 2.2 實作詞彙多樣性指標（MTLD、VOCD-D via lexical-diversity）
- [x] 2.3 實作詞頻分佈分析（K1/K2/AWL 內建詞表 + spaCy lemmatization）
- [x] 2.4 實作自我修正偵測（pattern matching）
- [x] 2.5 實作語法分析（從句比例、時態多樣性 via spaCy）
- [x] 2.6 實作短文本/空文本防護邏輯

## 3. Assessment Service（評估 pipeline）

- [x] 3.1 建立 assessment/service.py — AssessmentService 骨架（evaluate 方法）
- [x] 3.2 實作雙層 pipeline 編排（NLP → Claude → 後處理）
- [x] 3.3 實作 Claude Agent 質性分析整合（transcript_evaluator skill 呼叫 + 結果解析）
- [x] 3.4 實作 user_vocabulary 更新邏輯（根據 Claude 輸出的 new_words）
- [x] 3.5 實作 level_snapshot 觸發邏輯（每 5 次評估聚合）

## 4. REST API Endpoints

- [x] 4.1 實作 GET /api/assessment/{assessment_id} — 單一評估查詢
- [x] 4.2 實作 GET /api/assessment/user/{user_id}/history — 評估歷史（分頁）
- [x] 4.3 實作 GET /api/assessment/user/{user_id}/vocabulary — 詞彙統計
- [x] 4.4 實作 GET /api/assessment/user/{user_id}/progress — 成長追蹤

## 5. BYOA 整合

- [x] 5.1 實作 get_user_history tool（查詢使用者能力摘要供 Agent 使用）
- [x] 5.2 修改 ConversationManager.end_conversation() — 對話結束觸發評估

## 6. 驗證

- [x] 6.1 撰寫 .feature 檔（nlp-metrics、transcript-evaluation、assessment-history、conversation-lifecycle 修改）
- [x] 6.2 撰寫 pytest-bdd step definitions
- [x] 6.3 確認 ruff check + ruff format + pyright 全部通過
- [x] 6.4 Design review