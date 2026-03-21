## ADDED Requirements

### Requirement: GeminiHandler 音訊串流
系統 SHALL 實作 `GeminiHandler(AsyncStreamHandler)` 子類別，橋接 FastRTC WebRTC 音訊與 Gemini Live API。

- `receive(frame)` 接收使用者音訊，轉發至 Gemini Live session
- `emit()` 從 Gemini 回應佇列取出音訊，回傳給 FastRTC
- `copy()` 建立獨立實例供每個 WebRTC 連線使用
- `start_up()` 建立 Gemini Live session 並啟動 receiver loop

#### Scenario: 正常音訊雙向串流
- **WHEN** WebRTC 連線建立且 Gemini session 就緒
- **THEN** 使用者音訊 SHALL 透過 `send_realtime_input()` 傳送至 Gemini
- **AND** Gemini 回應音訊 SHALL 透過 `emit()` 回傳給使用者

#### Scenario: 每個連線獨立 handler
- **WHEN** 新的 WebRTC 連線建立
- **THEN** `copy()` SHALL 建立獨立的 GeminiHandler 實例
- **AND** 新實例 SHALL 有獨立的 Gemini session 和 transcript buffer

### Requirement: Transcript 收集
系統 SHALL 在對話期間即時收集 Gemini Live API 的 `input_transcription`（使用者）和 `output_transcription`（模型）事件。

- Transcript 以 `[{role, text, timestamp}]` 格式儲存於記憶體
- 僅在 `finished=True` 時記錄完整句
- 對話結束時一次回傳完整 transcript

#### Scenario: 收集使用者 transcript
- **WHEN** Gemini 送出 `input_transcription` 事件且 `finished=True`
- **THEN** 系統 SHALL 記錄 `{role: "user", text: <transcribed_text>, timestamp: <iso>}`

#### Scenario: 收集模型 transcript
- **WHEN** Gemini 送出 `output_transcription` 事件且 `finished=True`
- **THEN** 系統 SHALL 記錄 `{role: "model", text: <transcribed_text>, timestamp: <iso>}`

#### Scenario: 忽略未完成的 transcript
- **WHEN** Gemini 送出 transcript 事件且 `finished=False`
- **THEN** 系統 SHALL 不記錄此事件

### Requirement: Gemini session 配置
系統 SHALL 以下列參數建立 Gemini Live session：
- `response_modalities: ["AUDIO"]`
- `input_audio_transcription: {}` 啟用
- `output_audio_transcription: {}` 啟用
- `system_instruction`: 來自 scenario_designer 生成的 prompt

#### Scenario: 使用 system instruction 建立 session
- **WHEN** 建立 Gemini Live session
- **THEN** session 的 `system_instruction` SHALL 為 scenario_designer 產出的情境 prompt

### Requirement: Gemini 斷線處理
系統 SHALL 在 Gemini Live session 意外斷線時，保留已收集的 transcript 並通知上層。

#### Scenario: Gemini session 斷線
- **WHEN** Gemini Live session 的 receiver loop 發生例外
- **THEN** 系統 SHALL 保留已收集的 transcript
- **AND** 系統 SHALL 透過回呼通知 ConversationManager 設定狀態為 failed

### Requirement: FastRTC Mount
系統 SHALL 將 `Stream` 掛載至 FastAPI app，路徑為 `/api/conversation/rtc`。

#### Scenario: WebRTC signaling endpoint 可用
- **WHEN** FastAPI app 啟動
- **THEN** `POST /api/conversation/rtc/webrtc/offer` endpoint SHALL 存在且可接受 SDP offer
