## Why

對話結束後缺乏能力回饋迴圈。目前 Conversation Service 能收集 transcript，但沒有分析機制將對話表現轉化為可追蹤的能力指標。Assessment Service 是學習迴圈的關鍵一環——沒有它，系統無法知道使用者的程度、無法調整難度、無法推薦素材。

## What Changes

- 新增 NLP Pipeline：自動計算 transcript 的量化指標（MTLD、VOCD-D、K1/K2/AWL 分佈、句長、從句比例、時態多樣性、自我修正偵測）
- 新增 Claude Agent 質性分析：transcript_evaluator skill，結合 NLP metrics + transcript 產出 CEFR 等級與改善建議
- 新增 Assessment Repository：assessments 表寫入、user_vocabulary 更新、level_snapshot 聚合
- 新增 REST API：查詢評估結果、使用者歷史、詞彙統計、成長追蹤
- 新增 get_user_history Tool：供 BYOA Agent 查詢使用者能力摘要

## Capabilities

### New Capabilities
- `nlp-metrics`: NLP 量化指標計算 pipeline（MTLD、VOCD-D、K1/K2/AWL、句長、從句比例、時態多樣性、自我修正偵測）
- `transcript-evaluation`: Claude Agent 質性分析 + 雙層評估 pipeline 整合（NLP → Claude → 後處理）
- `assessment-history`: 評估結果儲存、查詢、使用者詞彙追蹤、level snapshot 聚合、REST API

### Modified Capabilities
- `conversation-lifecycle`: 對話結束後需觸發評估 pipeline（新增 assessing → completed 狀態轉換的實際處理）

## Impact

- 新增 `assessment/` 模組：`nlp.py`、`service.py`、`repository.py`、`schemas.py`、`router.py`
- 新增依賴：`lexical_diversity`（MTLD/VOCD-D）、`spacy`（語法分析）
- 修改 `conversation/manager.py`：對話結束後觸發評估
- DB：新增 `assessments`、`user_vocabulary`、`user_level_snapshots` 表
- BYOA：新增 `get_user_history` tool、`transcript_evaluator` skill
