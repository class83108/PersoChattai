## ADDED Requirements

### Requirement: Source selection to start conversation
使用者 SHALL 能選擇素材來源（卡片 / 自由主題）來啟動一場新對話。

#### Scenario: Start conversation from card
- **WHEN** 使用者選擇 source_type 為 card 並輸入 source_ref
- **THEN** 呼叫 `/api/conversation/start`，UI 進入 preparing 狀態

#### Scenario: Start conversation with free topic
- **WHEN** 使用者選擇 source_type 為 free_topic 並輸入主題
- **THEN** 呼叫 `/api/conversation/start`，UI 進入 preparing 狀態

#### Scenario: Block when active conversation exists
- **WHEN** API 回傳 409（已有進行中對話）
- **THEN** 顯示提示「你已有進行中的對話」

### Requirement: State indicator shows current conversation status
對話區域 SHALL 根據 conversation status 顯示對應的 UI 狀態。

#### Scenario: Preparing state
- **WHEN** 對話狀態為 preparing
- **THEN** 顯示「正在準備對話情境...」和 loading 動畫

#### Scenario: Connecting state
- **WHEN** 對話狀態為 connecting
- **THEN** 顯示「正在建立語音連線...」和 loading 動畫

#### Scenario: Active state
- **WHEN** 對話狀態為 active
- **THEN** 顯示計時器、音量指示器、結束對話按鈕

#### Scenario: Assessing state
- **WHEN** 對話狀態為 assessing
- **THEN** 顯示「正在分析對話內容...」和 loading 動畫

#### Scenario: Completed state
- **WHEN** 對話狀態為 completed
- **THEN** 顯示完成提示，引導使用者查看評估結果

#### Scenario: Failed state with retry
- **WHEN** 對話狀態為 failed
- **THEN** 顯示「連線失敗」錯誤訊息和重試按鈕

### Requirement: Microphone permission check
系統 SHALL 在啟動對話前檢查麥克風權限。

#### Scenario: Microphone not available
- **WHEN** 瀏覽器不支援 getUserMedia 或使用者拒絕權限
- **THEN** 顯示提示訊息，阻止啟動對話
