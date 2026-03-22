## ADDED Requirements

### Requirement: Conversation timer
對話進行中 SHALL 顯示計時器，從 active 狀態開始計時。

#### Scenario: Timer starts on active
- **WHEN** 對話進入 active 狀態
- **THEN** 計時器從 00:00 開始計時，每秒更新

#### Scenario: Timer stops on end
- **WHEN** 對話結束（進入 assessing / completed / failed / cancelled）
- **THEN** 計時器停止計時

### Requirement: End conversation button
對話進行中 SHALL 顯示「結束對話」按鈕。

#### Scenario: End active conversation
- **WHEN** 使用者點擊「結束對話」
- **THEN** 呼叫 `/api/conversation/{id}/end`，UI 進入 assessing 狀態

### Requirement: Cancel conversation button
對話進行中 SHALL 顯示「取消」按鈕。

#### Scenario: Cancel conversation
- **WHEN** 使用者點擊「取消」
- **THEN** 呼叫 `/api/conversation/{id}/cancel`，UI 回到初始狀態

### Requirement: Audio activity indicator
對話進行中 SHALL 顯示簡單的音量指示器，表示麥克風正在接收聲音。

#### Scenario: Audio indicator pulses during speech
- **WHEN** 使用者正在說話（麥克風有音訊輸入）
- **THEN** 音量指示器有視覺變化（脈動動畫）

#### Scenario: Audio indicator idle during silence
- **WHEN** 使用者沒有說話
- **THEN** 音量指示器處於靜止狀態
