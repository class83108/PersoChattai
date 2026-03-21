Feature: NLP 量化指標計算
  作為系統
  我想要從 transcript 文字計算量化語言指標
  以便為能力評估提供客觀數據基礎

  Rule: 完整指標計算

    Scenario: 正常長度 transcript 計算完整指標
      Given 一段包含多句英文的 transcript 至少 100 tokens
      When 執行 NLP 分析
      Then 回傳 NlpMetrics 包含 mtld vocd_d k1_ratio k2_ratio awl_ratio
      And 回傳 NlpMetrics 包含 avg_sentence_length conjunction_ratio self_correction_count
      And 回傳 NlpMetrics 包含 subordinate_clause_ratio tense_diversity grammar_error_count

  Rule: 詞彙多樣性指標

    Scenario: MTLD 計算
      Given 一段至少 50 tokens 的英文 transcript
      When 執行 NLP 分析
      Then mtld 為正數

    Scenario: VOCD-D 計算
      Given 一段至少 50 tokens 的英文 transcript
      When 執行 NLP 分析
      Then vocd_d 為正數

  Rule: 詞頻分佈分析

    Scenario: K1 K2 AWL 比例計算
      Given 一段包含混合難度詞彙的 transcript
      When 執行 NLP 分析
      Then k1_ratio 和 k2_ratio 和 awl_ratio 各自介於 0.0 至 1.0
      And 三者之和不超過 1.0

  Rule: 自我修正偵測

    Scenario: 偵測多個自我修正
      Given transcript 包含 "I went to... I mean, I was going to the store. No wait, the mall."
      When 執行 NLP 分析
      Then self_correction_count 至少為 2

    Scenario: 無自我修正
      Given transcript 包含 "I enjoy reading books every day."
      When 執行 NLP 分析
      Then self_correction_count 為 0

  Rule: 語法分析

    Scenario: 從句比例計算
      Given transcript 包含 "Although it was raining, I went out because I needed groceries."
      When 執行 NLP 分析
      Then subordinate_clause_ratio 大於 0

    Scenario: 時態多樣性計算
      Given transcript 包含 "I went to the store yesterday. I have been studying English. I will travel next week."
      When 執行 NLP 分析
      Then tense_diversity 大於 1

  Rule: 輸入邊界

    Scenario: 短文本 MTLD 和 VOCD-D 回傳 None
      Given 一段少於 50 tokens 的短 transcript
      When 執行 NLP 分析
      Then mtld 為 None
      And vocd_d 為 None
      And 其餘指標正常計算

    Scenario: 空字串
      Given transcript 為空字串
      When 執行 NLP 分析
      Then 所有數值指標為 0 或 None

  Rule: Edge Cases

    Scenario: 全重複詞彙
      Given transcript 為 "the the the the the the the the the the" 重複 20 次
      When 執行 NLP 分析
      Then mtld 小於 20

    Scenario: 高比例學術詞彙
      Given transcript 包含大量學術詞彙如 "analyze hypothesis methodology empirical"
      When 執行 NLP 分析
      Then awl_ratio 大於 0.1

  Rule: 輸出契約

    Scenario: NlpMetrics 所有欄位型別正確
      Given 一段正常長度的 transcript
      When 執行 NLP 分析
      Then mtld 為 float 或 None
      And vocd_d 為 float 或 None
      And k1_ratio k2_ratio awl_ratio 為 float
      And avg_sentence_length 為 float
      And conjunction_ratio 為 float
      And subordinate_clause_ratio 為 float
      And self_correction_count 為 int
      And tense_diversity 為 int
      And grammar_error_count 為 int

    Scenario: ratio 值範圍正確
      Given 一段正常長度的 transcript
      When 執行 NLP 分析
      Then 所有 ratio 值介於 0.0 至 1.0
      And 所有 count 值大於等於 0
