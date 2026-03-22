## ADDED Requirements

### Requirement: Async engine 管理
系統 SHALL 在 `database/engine.py` 提供 async engine 與 session factory 的初始化與清理。

#### Scenario: 建立 async engine
- **WHEN** 呼叫初始化函式並傳入 DB URL
- **THEN** 系統 SHALL 建立 `AsyncEngine`，URL scheme 為 `postgresql+asyncpg://`
- **AND** 建立 `async_sessionmaker` 綁定該 engine

#### Scenario: 關閉 engine
- **WHEN** app shutdown
- **THEN** 系統 SHALL 呼叫 `engine.dispose()` 釋放連線

### Requirement: Session-per-request pattern
系統 SHALL 提供 FastAPI dependency 以 session-per-request 模式注入 `AsyncSession`。

#### Scenario: 每個 request 取得獨立 session
- **WHEN** FastAPI endpoint 透過 `Depends(get_session)` 取得 session
- **THEN** 該 session SHALL 在 request 結束時自動 close
- **AND** 若 endpoint 未拋出例外，session SHALL 自動 commit

#### Scenario: Request 發生例外時 rollback
- **WHEN** endpoint 處理中拋出例外
- **THEN** session SHALL 自動 rollback
- **AND** 不會有 partial write 殘留

### Requirement: Repository 接受 AsyncSession 注入
所有 repository 的 constructor SHALL 接受 `AsyncSession` 而非 pool。

#### Scenario: Repository 使用注入的 session
- **WHEN** repository 執行查詢
- **THEN** 它 SHALL 使用注入的 `AsyncSession`
- **AND** 不自行管理 connection 或 transaction
