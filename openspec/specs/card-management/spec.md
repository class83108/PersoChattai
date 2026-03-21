## ADDED Requirements

### Requirement: 建立卡片
系統 SHALL 支援透過 repository 建立學習卡片，卡片包含 title、summary、keywords、dialogue_snippets、difficulty_level、tags、source_type、source_url 欄位。

#### Scenario: 成功建立卡片
- **WHEN** 提供完整的卡片資料（title、summary、source_type）呼叫 repository.create()
- **THEN** 系統將卡片寫入 cards 表，回傳包含自動產生的 id 和 created_at 的卡片資料

#### Scenario: source_url 重複時不重複建立
- **WHEN** 建立卡片時提供的 source_url 已存在於 cards 表
- **THEN** 系統 SHALL 忽略此次寫入（ON CONFLICT DO NOTHING），不拋出錯誤

### Requirement: 查詢卡片列表
系統 SHALL 提供 `GET /api/content/cards` endpoint，支援依多種條件篩選卡片。

#### Scenario: 無篩選條件查詢
- **WHEN** 呼叫 `GET /api/content/cards` 不帶任何 query parameter
- **THEN** 系統回傳所有卡片，按 created_at DESC 排序，預設分頁 limit=20

#### Scenario: 依 source_type 篩選
- **WHEN** 呼叫 `GET /api/content/cards?source_type=podcast_allearsenglish`
- **THEN** 系統只回傳 source_type 為 podcast_allearsenglish 的卡片

#### Scenario: 依 difficulty_level 篩選
- **WHEN** 呼叫 `GET /api/content/cards?difficulty=B1`
- **THEN** 系統只回傳 difficulty_level 為 B1 的卡片

#### Scenario: 依 tag 篩選
- **WHEN** 呼叫 `GET /api/content/cards?tag=business`
- **THEN** 系統只回傳 tags 陣列包含 "business" 的卡片

#### Scenario: 依關鍵字搜尋
- **WHEN** 呼叫 `GET /api/content/cards?keyword=interview`
- **THEN** 系統回傳 title 或 summary 中包含 "interview"（case-insensitive）的卡片

#### Scenario: 分頁查詢
- **WHEN** 呼叫 `GET /api/content/cards?limit=5&offset=10`
- **THEN** 系統回傳第 11-15 筆卡片

### Requirement: 查詢單一卡片
系統 SHALL 提供 `GET /api/content/cards/{card_id}` endpoint。

#### Scenario: 卡片存在
- **WHEN** 呼叫 `GET /api/content/cards/{card_id}` 且該 card_id 存在
- **THEN** 系統回傳該卡片的完整資料

#### Scenario: 卡片不存在
- **WHEN** 呼叫 `GET /api/content/cards/{card_id}` 且該 card_id 不存在
- **THEN** 系統回傳 HTTP 404
