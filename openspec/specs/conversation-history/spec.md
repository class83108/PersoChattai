## ADDED Requirements

### Requirement: Conversation history list
Role Play 頁面 SHALL 顯示使用者的對話歷史列表。

#### Scenario: History loads via HTMX
- **WHEN** 使用者訪問 Role Play 頁面
- **THEN** 透過 HTMX 載入對話歷史列表

#### Scenario: History item shows key info
- **WHEN** 對話歷史列表載入
- **THEN** 每筆紀錄顯示日期、素材來源、對話狀態 badge、持續時間

#### Scenario: Empty history
- **WHEN** 使用者沒有任何對話紀錄
- **THEN** 顯示空狀態提示「還沒有對話紀錄，開始你的第一場 Role Play 吧」

### Requirement: User ID persistence
系統 SHALL 使用 localStorage 存儲 user_id（UUID），作為暫時的使用者識別。

#### Scenario: First visit generates user ID
- **WHEN** 使用者首次訪問且 localStorage 無 user_id
- **THEN** 生成新的 UUID 並存入 localStorage

#### Scenario: Subsequent visits reuse user ID
- **WHEN** 使用者再次訪問且 localStorage 有 user_id
- **THEN** 使用既有的 user_id
