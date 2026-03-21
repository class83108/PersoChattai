## ADDED Requirements

### Requirement: NLP 量化指標計算
系統 SHALL 提供 `NlpAnalyzer` 模組，接收 transcript 文字，回傳結構化的量化指標。所有指標計算 SHALL 為純函式，不涉及 IO。

#### Scenario: 計算完整指標
- **WHEN** 輸入一段包含多句英文的 transcript 文字（≥50 tokens）
- **THEN** 系統 SHALL 回傳包含以下指標的 `NlpMetrics` 物件：
  - `mtld`: float（Measure of Textual Lexical Diversity）
  - `vocd_d`: float（隨機取樣 TTR 平均值）
  - `k1_ratio`: float（前 1000 常用字佔比）
  - `k2_ratio`: float（1001-2000 常用字佔比）
  - `awl_ratio`: float（學術詞彙佔比）
  - `avg_sentence_length`: float（平均句長，tokens per sentence）
  - `conjunction_ratio`: float（連接詞比例）
  - `self_correction_count`: int（自我修正次數）
  - `subordinate_clause_ratio`: float（從句比例）
  - `tense_diversity`: int（使用的時態種類數）
  - `grammar_error_count`: int（語法錯誤數，spaCy 偵測）

#### Scenario: 短文本處理
- **WHEN** 輸入的 transcript 文字少於 50 tokens
- **THEN** `mtld` 和 `vocd_d` SHALL 回傳 None
- **AND** 其餘指標 SHALL 正常計算

#### Scenario: 空文本處理
- **WHEN** 輸入為空字串
- **THEN** 系統 SHALL 回傳所有數值指標為 0 或 None 的 `NlpMetrics`

### Requirement: 詞彙多樣性指標
系統 SHALL 使用 `lexical-diversity` 套件計算 MTLD 和 VOCD-D。

#### Scenario: MTLD 計算
- **WHEN** 輸入一段至少 50 tokens 的英文文字
- **THEN** 系統 SHALL 回傳 MTLD 值（float > 0）

#### Scenario: VOCD-D 計算
- **WHEN** 輸入一段至少 50 tokens 的英文文字
- **THEN** 系統 SHALL 回傳 VOCD-D 值（float > 0）

### Requirement: 詞頻分佈分析
系統 SHALL 將 transcript 中的單字經 lemmatization 後，分類至 K1（前 1000）、K2（1001-2000）、AWL（學術詞彙）三個詞頻等級，計算各等級佔比。

#### Scenario: 詞頻分佈計算
- **WHEN** 輸入含有混合難度詞彙的 transcript
- **THEN** 系統 SHALL 回傳 k1_ratio + k2_ratio + awl_ratio，三者之和 ≤ 1.0
- **AND** 每個 ratio SHALL 介於 0.0 至 1.0 之間

### Requirement: 自我修正偵測
系統 SHALL 偵測 transcript 中的自我修正模式，包含 "I mean"、"sorry"、"no wait"、"let me rephrase"、"actually" 等 pattern。

#### Scenario: 偵測自我修正
- **WHEN** transcript 包含 "I mean, I went to... no wait, I was going to the store"
- **THEN** `self_correction_count` SHALL ≥ 2

#### Scenario: 無自我修正
- **WHEN** transcript 不包含任何自我修正 pattern
- **THEN** `self_correction_count` SHALL 為 0

### Requirement: 語法分析
系統 SHALL 使用 spaCy 分析句型結構，計算從句比例和時態多樣性。

#### Scenario: 從句比例計算
- **WHEN** 輸入包含主句和從句的 transcript
- **THEN** `subordinate_clause_ratio` SHALL > 0

#### Scenario: 時態多樣性計算
- **WHEN** transcript 使用多種時態（如 past simple、present perfect）
- **THEN** `tense_diversity` SHALL > 1
