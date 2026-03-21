Feature: Transcript 評估 Pipeline
  作為系統
  我想要在對話結束後自動分析 transcript 產出能力評估
  以便追蹤使用者的英文能力成長

  Background:
    Given 測試用 AssessmentService 已初始化

  Rule: 評估 Happy Path

    Scenario: 完整雙層評估流程
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then NLP 量化指標計算完成
      And Claude 質性分析完成
      And assessment 記錄寫入 DB
      And user_vocabulary 更新完成

    Scenario: 評估結果包含 CEFR 等級
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳 cefr_level "B1"
      When 執行評估 pipeline
      Then assessment 的 cefr_level 為 "B1"

  Rule: 錯誤處理

    Scenario: Claude API 失敗時保留 NLP 指標
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 拋出例外
      When 執行評估 pipeline
      Then assessment 記錄仍寫入 DB
      And assessment 包含 NLP 量化指標
      And assessment 的質性分析欄位為 null
      And 記錄 error log

    Scenario: Claude 回傳格式錯誤時 graceful degradation
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳無法解析的格式
      When 執行評估 pipeline
      Then assessment 記錄仍寫入 DB
      And assessment 的質性分析欄位為 null

  Rule: 輸入邊界

    Scenario: 空 transcript 跳過評估
      Given transcript 為空
      When 執行評估 pipeline
      Then 不建立 assessment 記錄
      And 不更新 user_vocabulary

    Scenario: 極短 transcript 仍完成評估
      Given 一段極短的 transcript 只有 "Hello, nice to meet you."
      When 執行評估 pipeline
      Then assessment 記錄寫入 DB
      And mtld 和 vocd_d 為 None

  Rule: 詞彙更新

    Scenario: 新增詞彙至詞彙庫
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳 new_words ["pragmatic", "nuanced"]
      And 使用者詞彙庫中沒有這些詞
      When 執行評估 pipeline
      Then user_vocabulary 新增 2 筆記錄
      And 每筆 occurrence_count 為 1

    Scenario: 已知詞彙累加次數
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳 new_words ["pragmatic"]
      And 使用者詞彙庫中已有 "pragmatic" occurrence_count 為 3
      When 執行評估 pipeline
      Then "pragmatic" 的 occurrence_count 變為 4
      And first_seen_at 不變

    Scenario: new_words 為空列表
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳 new_words 為空列表
      When 執行評估 pipeline
      Then user_vocabulary 不新增任何記錄

  Rule: Level Snapshot 觸發

    Scenario: 第 5 次評估觸發 snapshot
      Given 使用者已有 4 次評估記錄
      And 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then 產生 level_snapshot
      And users.current_level 更新

    Scenario: 第 4 次評估不觸發 snapshot
      Given 使用者已有 3 次評估記錄
      And 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then 不產生 level_snapshot

    Scenario: 第 10 次評估觸發 snapshot
      Given 使用者已有 9 次評估記錄
      And 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then 產生 level_snapshot

  Rule: 狀態寫入正確性

    Scenario: assessment 記錄包含完整欄位
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then assessment 包含 conversation_id 和 user_id
      And assessment 包含所有 NLP 指標欄位
      And assessment 包含 cefr_level lexical_assessment fluency_assessment grammar_assessment
      And assessment 包含 suggestions 和 new_words

  Rule: 輸出契約

    Scenario: cefr_level 為有效 CEFR 等級
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then assessment 的 cefr_level 為 A1 A2 B1 B2 C1 C2 其中之一

    Scenario: suggestions 為字串列表
      Given 一段有效的對話 transcript
      And 模擬 Claude Agent 回傳有效的評估結果
      When 執行評估 pipeline
      Then assessment 的 suggestions 為非空的字串列表
