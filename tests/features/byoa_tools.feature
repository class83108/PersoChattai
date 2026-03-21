Feature: BYOA Tools
  作為 BYOA Agent
  我想要 透過 tool calling 存取 Service 層資料
  以便 在摘要、情境設計、評估過程中查詢和建立資料

  Rule: query_cards tool 依條件查詢素材卡片

    Scenario: 依難度查詢卡片
      Given 資料庫有以下卡片
        | title            | difficulty_level | source_type          | tags      |
        | Business Meeting | B1               | podcast_allearsenglish | business  |
        | BBC News Chat    | B2               | podcast_bbc          | news      |
        | Easy Greetings   | A1               | podcast_allearsenglish | basic     |
      When 呼叫 query_cards tool 帶入 difficulty_level "B1"
      Then 回傳 1 張卡片且標題為 "Business Meeting"

    Scenario: 複合條件查詢
      Given 資料庫有以下卡片
        | title            | difficulty_level | source_type          | tags      |
        | Business Meeting | B1               | podcast_allearsenglish | business  |
        | BBC Business     | B2               | podcast_bbc          | business  |
        | BBC News Chat    | B2               | podcast_bbc          | news      |
      When 呼叫 query_cards tool 帶入 source_type "podcast_bbc" 和 tag "business"
      Then 回傳 1 張卡片且標題為 "BBC Business"

    Scenario: 無符合條件的卡片
      Given 資料庫有以下卡片
        | title            | difficulty_level | source_type          | tags      |
        | Business Meeting | B1               | podcast_allearsenglish | business  |
      When 呼叫 query_cards tool 帶入 difficulty_level "C2"
      Then 回傳空列表

  Rule: create_card tool 建立學習卡片

    Scenario: 成功建立卡片
      Given 一個可寫入的卡片 repository
      When 呼叫 create_card tool 帶入完整參數
        | field            | value                    |
        | title            | Podcast Summary          |
        | summary          | A great episode.         |
        | keywords         | [{"word": "negotiate"}]  |
        | source_type      | podcast_allearsenglish   |
        | difficulty_level | B1                       |
      Then 卡片成功寫入且回傳含 "id" 欄位

    Scenario: 缺少必填欄位
      Given 一個可寫入的卡片 repository
      When 呼叫 create_card tool 缺少 title 欄位
      Then 回傳錯誤訊息包含 "title"

  Rule: get_user_history tool 查詢使用者歷史

    Scenario: 有歷史資料的使用者
      Given 使用者有 3 次評估紀錄和詞彙資料
      When 呼叫 get_user_history tool 帶入該使用者 ID
      Then 回傳包含 "snapshot" 和 "recent_assessments" 和 "vocabulary_stats"
      And "recent_assessments" 有 3 筆紀錄

    Scenario: 新使用者無歷史
      Given 使用者無任何評估紀錄
      When 呼叫 get_user_history tool 帶入該使用者 ID
      Then 回傳 "snapshot" 為 null
      And "recent_assessments" 為空列表

  Rule: Tool registry 按 Agent 角色組裝

    Scenario: Content agent 只包含 create_card
      Given 已組裝的 tool registries
      When 查詢 content agent 的 tool 列表
      Then 只包含 "create_card"

    Scenario: Conversation agent 包含 query_cards 和 get_user_history
      Given 已組裝的 tool registries
      When 查詢 conversation agent 的 tool 列表
      Then 包含 "query_cards" 和 "get_user_history"

    Scenario: Assessment agent 只包含 get_user_history
      Given 已組裝的 tool registries
      When 查詢 assessment agent 的 tool 列表
      Then 只包含 "get_user_history"
