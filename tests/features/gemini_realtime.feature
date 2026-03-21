Feature: Gemini 即時音訊串流
  作為系統
  我想要透過 GeminiHandler 橋接 FastRTC 與 Gemini Live API
  以便實現使用者與 Gemini 的即時語音對話並收集 transcript

  Rule: 音訊雙向串流

    Scenario: 使用者音訊放入 input queue
      Given GeminiHandler 已建立且 session 就緒
      When 收到使用者音訊 frame
      Then 音訊應被放入 input queue

    Scenario: Gemini 回應音訊回傳給使用者
      Given GeminiHandler 已建立且 session 就緒
      And output queue 中有音訊資料
      When 呼叫 emit
      Then 應回傳音訊 frame 格式為 (sample_rate, ndarray)

    Scenario: 空音訊 frame 不放入 queue
      Given GeminiHandler 已建立且 session 就緒
      When 收到空的音訊 frame
      Then input queue 應為空

  Rule: Handler 生命週期

    Scenario: start_up 建立 Gemini session 並啟動 stream
      Given GeminiHandler 已建立且有合法的 Gemini client
      When 呼叫 start_up
      Then 應透過 client.aio.live.connect 建立 session
      And 應啟動 stream loop 處理音訊

    Scenario: shutdown 停止 stream loop
      Given GeminiHandler 已建立且 session 就緒
      When 呼叫 shutdown
      Then quit event 應被設定
      And stream generator 應停止 yield

    Scenario: emit 在連線關閉後回傳 None
      Given GeminiHandler 已建立且 session 就緒
      When 連線已關閉且 output queue 為空
      Then emit 應回傳 None

  Rule: 每個連線獨立 handler

    Scenario: copy 建立獨立實例
      Given GeminiHandler 已建立
      When 呼叫 copy
      Then 應建立新的 GeminiHandler 實例
      And 新實例應有獨立的 transcript buffer
      And 新實例應有獨立的 input queue 和 output queue

    Scenario: 不同實例的 transcript 互不影響
      Given 兩個獨立的 GeminiHandler 實例
      When 實例 A 收集到一筆 transcript
      Then 實例 B 的 transcript buffer 應為空

  Rule: Transcript 收集

    Scenario: 收集使用者 transcript
      Given GeminiHandler 已建立且 session 就緒
      When Gemini 送出 input_transcription 事件且 finished 為 True 內容為 "Hello"
      Then transcript buffer 應包含一筆 role 為 "user" text 為 "Hello" 的記錄
      And 該記錄應包含 timestamp

    Scenario: 收集模型 transcript
      Given GeminiHandler 已建立且 session 就緒
      When Gemini 送出 output_transcription 事件且 finished 為 True 內容為 "Hi there"
      Then transcript buffer 應包含一筆 role 為 "model" text 為 "Hi there" 的記錄
      And 該記錄應包含 timestamp

    Scenario: 忽略未完成的 transcript
      Given GeminiHandler 已建立且 session 就緒
      When Gemini 送出 input_transcription 事件且 finished 為 False 內容為 "Hel"
      Then transcript buffer 應為空

    Scenario: 多輪對話 transcript 按順序累積
      Given GeminiHandler 已建立且 session 就緒
      When 依序收到以下完成的 transcript 事件:
        | role  | text        |
        | user  | Hello       |
        | model | Hi there    |
        | user  | How are you |
      Then transcript buffer 應包含 3 筆記錄且順序正確

  Rule: Gemini session 配置

    Scenario: 使用 system instruction 建立 LiveConnectConfig
      Given scenario_designer 產出 system instruction "You are a hotel receptionist"
      When 建立 Gemini session 配置
      Then config 的 system_instruction 應為 "You are a hotel receptionist"
      And config 的 response_modalities 應包含 AUDIO
      And config 應啟用 input_audio_transcription
      And config 應啟用 output_audio_transcription

  Rule: 錯誤處理

    Scenario: start_up 中 Gemini connect 失敗
      Given GeminiHandler 已建立且 Gemini client 的 connect 會失敗
      When 呼叫 start_up
      Then 應透過回呼通知 ConversationManager 設定狀態為 failed

    Scenario: stream loop 發生例外時保留 transcript 並通知
      Given GeminiHandler 已建立且已收集 2 筆 transcript
      When stream loop 發生例外
      Then 已收集的 2 筆 transcript 應被保留
      And 應透過回呼通知 ConversationManager

  Rule: 啟動防護

    Scenario: session 未就緒時收到音訊應安全忽略
      Given GeminiHandler 已建立但 start_up 尚未完成
      When 收到使用者音訊 frame
      Then 不應拋出例外
      And input queue 應為空

    Scenario: 對話結束後收到殘留事件應安全忽略
      Given GeminiHandler 已建立但對話已結束
      When receiver loop 收到殘留的 transcript 事件
      Then 不應寫入 transcript buffer
      And 不應拋出例外
