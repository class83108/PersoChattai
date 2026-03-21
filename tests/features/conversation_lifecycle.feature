Feature: 對話生命週期管理
  作為系統
  我想要管理對話的完整生命週期
  以便確保對話狀態正確轉換、資源正確清理、transcript 正確儲存

  Rule: 正常對話狀態流程

    Scenario: 完整對話流程依序經過所有狀態
      Given ConversationManager 已初始化
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 對話狀態依序經過 preparing、connecting、active
      When 使用者結束對話
      Then 對話狀態轉為 assessing
      And 最終狀態轉為 completed

    Scenario: 建立對話時呼叫 scenario_designer 生成 system instruction
      Given ConversationManager 已初始化
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 系統應以素材內容呼叫 scenario_designer
      And 產出的 system instruction 應用於 Gemini session 配置

    Scenario: 根據自由主題生成情境
      Given ConversationManager 已初始化
      When 使用者 "user-1" 以 source_type "free_topic" 和 source_ref "travel" 啟動對話
      Then 系統應以 "travel" 呼叫 scenario_designer

  Rule: 對話結束儲存 transcript

    Scenario: 正常結束時 transcript 寫入 DB
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      When 使用者結束對話
      Then transcript 應寫入 DB conversations.transcript
      And conversations.ended_at 應被更新

    Scenario: 異常結束時仍保留已收集的 transcript
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      When Gemini session 斷線
      Then 已收集的 transcript 應寫入 DB
      And 對話狀態轉為 failed

  Rule: 連線失敗

    Scenario: Gemini session 建立失敗
      Given ConversationManager 已初始化
      And Gemini session 建立會失敗
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 對話狀態轉為 failed

    Scenario: scenario_designer 呼叫失敗且重試仍失敗
      Given ConversationManager 已初始化
      And scenario_designer 會拋出 transient error
      And 重試 1 次仍失敗
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 對話狀態轉為 failed

    Scenario: scenario_designer transient error 重試成功
      Given ConversationManager 已初始化
      And scenario_designer 第一次呼叫會失敗但第二次會成功
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 對話應成功進入 connecting 狀態

  Rule: 使用者取消對話

    Scenario: active 狀態且有 transcript 時取消進入 assessing
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      When 使用者取消對話
      Then 對話狀態轉為 assessing

    Scenario: active 狀態但無 transcript 時取消進入 cancelled
      Given 使用者 "user-1" 有一個 active 對話但無 transcript
      When 使用者取消對話
      Then 對話狀態轉為 cancelled

    Scenario: preparing 階段取消
      Given 使用者 "user-1" 有一個 preparing 對話
      When 使用者取消對話
      Then 系統應清理進行中的資源
      And 對話狀態轉為 cancelled

    Scenario: connecting 階段取消
      Given 使用者 "user-1" 有一個 connecting 對話
      When 使用者取消對話
      Then 系統應中斷連線並清理資源
      And 對話狀態轉為 cancelled

  Rule: 時間上限

    Scenario: 對話持續 13 分鐘時發送警告
      Given 使用者 "user-1" 有一個 active 對話
      When 對話持續達 13 分鐘
      Then 系統應透過 data channel 發送時間警告

    Scenario: 對話持續 15 分鐘時自動結束
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      When 對話持續達 15 分鐘
      Then 系統應自動結束對話
      And transcript 應寫入 DB

    Scenario: 使用者在警告後主動結束不重複觸發
      Given 使用者 "user-1" 有一個 active 對話
      And 對話已發送 13 分鐘警告
      When 使用者結束對話
      Then 對話應正常結束一次
      And 不應觸發自動結束

  Rule: 靜默超時

    Scenario: 超過 2 分鐘無音訊輸入時自動結束
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      When 超過 2 分鐘未收到使用者音訊
      Then 系統應自動結束對話並儲存 transcript
      And 系統應透過 data channel 通知使用者

    Scenario: 收到音訊時重置靜默計時器
      Given 使用者 "user-1" 有一個 active 對話
      And 靜默計時器已過 1 分 50 秒
      When 收到使用者音訊
      Then 靜默計時器應重置為 2 分鐘

  Rule: 狀態轉換防護

    Scenario: 不允許非法狀態轉換
      Given 使用者 "user-1" 有一個 completed 對話
      When 嘗試將對話狀態轉為 active
      Then 系統應拒絕轉換並拋出錯誤

    Scenario: 每次狀態轉換同步寫入 DB
      Given ConversationManager 已初始化
      When 使用者 "user-1" 以 source_type "card" 和 source_ref "card-abc" 啟動對話
      Then 每次狀態變更都應寫入 DB conversations.status

  Rule: Transcript 寫入失敗處理

    Scenario: 寫入 DB 失敗後重試成功
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      And DB 寫入第一次會失敗但後續會成功
      When 使用者結束對話
      Then transcript 應在重試後成功寫入 DB
      And 對話狀態轉為 assessing

    Scenario: 重試全部失敗時標記 failed
      Given 使用者 "user-1" 有一個 active 對話且已收集 transcript
      And DB 寫入連續 3 次都會失敗
      When 使用者結束對話
      Then 系統應記錄錯誤日誌
      And 對話狀態轉為 failed
