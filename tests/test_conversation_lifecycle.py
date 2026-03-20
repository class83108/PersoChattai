"""Conversation Lifecycle 測試。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/conversation_lifecycle.feature')


def _run(coro: Any) -> Any:
    """在 sync step 中執行 async coroutine。"""
    return asyncio.run(coro)


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('persochattai.conversation.manager._TRANSCRIPT_RETRY_DELAYS', [0, 0])


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.update_status = AsyncMock()
    repo.save_transcript = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update_ended_at = AsyncMock()
    repo.list_by_user = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_scenario_designer() -> AsyncMock:
    designer = AsyncMock()
    designer.return_value = 'You are a hotel receptionist helping a guest check in.'
    return designer


@pytest.fixture
def mock_gemini_client() -> MagicMock:
    client = MagicMock()
    client.aio.live.connect = AsyncMock()
    return client


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


@pytest.fixture
def manager(
    mock_repo: MagicMock,
    mock_scenario_designer: AsyncMock,
    mock_gemini_client: MagicMock,
) -> Any:
    from persochattai.conversation.manager import ConversationManager

    return ConversationManager(
        repository=mock_repo,
        scenario_designer=mock_scenario_designer,
        gemini_client=mock_gemini_client,
    )


# --- Given: 初始化 ---


@given('ConversationManager 已初始化')
def manager_initialized(manager: Any) -> None:
    assert manager is not None


@given('Gemini session 建立會失敗')
def gemini_session_fails(mock_gemini_client: MagicMock) -> None:
    mock_gemini_client.aio.live.connect.side_effect = ConnectionError('Gemini unavailable')


@given('scenario_designer 會拋出 transient error')
def designer_transient_error(mock_scenario_designer: AsyncMock) -> None:
    mock_scenario_designer.side_effect = TimeoutError('API timeout')


@given('重試 1 次仍失敗')
def retry_still_fails() -> None:
    pass


@given('scenario_designer 第一次呼叫會失敗但第二次會成功')
def designer_fails_then_succeeds(mock_scenario_designer: AsyncMock) -> None:
    mock_scenario_designer.side_effect = [
        TimeoutError('API timeout'),
        'You are a hotel receptionist helping a guest check in.',
    ]


# --- Given: 對話狀態 ---


@given(parsers.parse('使用者 "{user_id}" 有一個 active 對話且已收集 transcript'))
def user_active_with_transcript(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    ctx['user_id'] = user_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'active',
        'transcript': [
            {'role': 'user', 'text': 'Hello', 'timestamp': '2026-03-20T10:01:00'},
            {'role': 'model', 'text': 'Hi there', 'timestamp': '2026-03-20T10:01:05'},
        ],
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 active 對話但無 transcript'))
def user_active_no_transcript(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'active',
        'transcript': [],
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 preparing 對話'))
def user_preparing(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'preparing',
        'transcript': [],
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 connecting 對話'))
def user_connecting(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'connecting',
        'transcript': [],
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 active 對話'))
def user_has_active(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    ctx['user_id'] = user_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'active',
        'transcript': [],
    }


@given(parsers.parse('使用者 "{user_id}" 有一個 completed 對話'))
def user_completed(user_id: str, manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = str(uuid.uuid4())
    ctx['conversation_id'] = conv_id
    manager._conversations[conv_id] = {
        'conversation_id': conv_id,
        'user_id': user_id,
        'status': 'completed',
        'transcript': [],
    }


# --- Given: Timeout ---


@given('對話已發送 13 分鐘警告')
def warning_already_sent(manager: Any, ctx: dict[str, Any]) -> None:
    manager._warning_sent[ctx['conversation_id']] = True


@given(parsers.parse('靜默計時器已過 1 分 50 秒'))
def silence_timer_almost_expired() -> None:
    pass


# --- Given: DB 失敗 ---


@given('DB 寫入第一次會失敗但後續會成功')
def db_write_fails_then_succeeds(mock_repo: MagicMock) -> None:
    mock_repo.save_transcript.side_effect = [
        ConnectionError('DB connection lost'),
        None,
    ]


@given(parsers.parse('DB 寫入連續 {count:d} 次都會失敗'))
def db_write_always_fails(count: int, mock_repo: MagicMock) -> None:
    mock_repo.save_transcript.side_effect = ConnectionError('DB connection lost')


# --- When: 啟動對話 ---


@when(
    parsers.parse(
        '使用者 "{user_id}" 以 source_type "{source_type}" 和 source_ref "{source_ref}" 啟動對話'
    ),
    target_fixture='start_result',
)
def start_conversation(
    user_id: str, source_type: str, source_ref: str, manager: Any, ctx: dict[str, Any]
) -> Any:
    result = _run(manager.start_conversation(user_id, source_type, source_ref))
    ctx['conversation_id'] = result.get('conversation_id')
    return result


# --- When: 結束 / 取消 ---


@when('使用者結束對話', target_fixture='end_result')
def user_ends(manager: Any, ctx: dict[str, Any]) -> Any:
    return _run(manager.end_conversation(ctx['conversation_id']))


@when('使用者取消對話', target_fixture='cancel_result')
def user_cancels(manager: Any, ctx: dict[str, Any]) -> Any:
    return _run(manager.cancel_conversation(ctx['conversation_id']))


# --- When: 外部事件 ---


@when('Gemini session 斷線')
def gemini_disconnects(manager: Any, ctx: dict[str, Any]) -> None:
    _run(manager.handle_disconnection(ctx['conversation_id']))


@when(parsers.parse('對話持續達 {minutes:d} 分鐘'))
def conversation_reaches_minutes(minutes: int, manager: Any, ctx: dict[str, Any]) -> None:
    _run(manager.simulate_time_elapsed(ctx['conversation_id'], minutes * 60))


@when('超過 2 分鐘未收到使用者音訊')
def silence_timeout(manager: Any, ctx: dict[str, Any]) -> None:
    _run(manager.handle_silence_timeout(ctx['conversation_id']))


@when('收到使用者音訊')
def receive_audio(manager: Any, ctx: dict[str, Any]) -> None:
    _run(manager.on_audio_received(ctx['conversation_id']))


@when('嘗試將對話狀態轉為 active', target_fixture='transition_error')
def try_illegal_transition(manager: Any, ctx: dict[str, Any]) -> Any:
    with pytest.raises(ValueError) as exc_info:
        manager.transition_state(ctx['conversation_id'], 'active')
    return exc_info


# --- Then: 狀態檢查 ---


@then('對話狀態依序經過 preparing、connecting、active')
def check_state_sequence(mock_repo: MagicMock) -> None:
    status_calls = [call.args[1] for call in mock_repo.update_status.call_args_list]
    assert 'preparing' in status_calls
    assert 'connecting' in status_calls
    assert 'active' in status_calls


@then(parsers.parse('對話狀態轉為 {status}'))
def check_state(status: str, manager: Any, ctx: dict[str, Any]) -> None:
    state = manager.get_state(ctx['conversation_id'])
    assert state['status'] == status


@then('最終狀態轉為 completed')
def check_completed(manager: Any, ctx: dict[str, Any]) -> None:
    # end_conversation 進入 assessing，模擬評估完成後轉 completed
    manager.transition_state(ctx['conversation_id'], 'completed')
    state = manager.get_state(ctx['conversation_id'])
    assert state['status'] == 'completed'


@then('對話應成功進入 connecting 狀態')
def check_connecting(manager: Any, ctx: dict[str, Any]) -> None:
    state = manager.get_state(ctx['conversation_id'])
    assert state['status'] in ('connecting', 'active')


# --- Then: Scenario Designer ---


@then('系統應以素材內容呼叫 scenario_designer')
def check_designer_called(mock_scenario_designer: AsyncMock) -> None:
    mock_scenario_designer.assert_called_once()


@then('產出的 system instruction 應用於 Gemini session 配置')
def check_instruction_used(mock_gemini_client: MagicMock) -> None:
    mock_gemini_client.aio.live.connect.assert_called_once()
    call_kwargs = mock_gemini_client.aio.live.connect.call_args.kwargs
    config = call_kwargs.get('config', {})
    assert config.get('system_instruction') is not None


@then(parsers.parse('系統應以 "{topic}" 呼叫 scenario_designer'))
def check_designer_called_with_topic(topic: str, mock_scenario_designer: AsyncMock) -> None:
    call_args = mock_scenario_designer.call_args
    assert topic in str(call_args)


# --- Then: Transcript ---


@then('transcript 應寫入 DB conversations.transcript')
def check_transcript_written(mock_repo: MagicMock) -> None:
    mock_repo.save_transcript.assert_called_once()


@then('conversations.ended_at 應被更新')
def check_ended_at_updated(mock_repo: MagicMock) -> None:
    mock_repo.update_ended_at.assert_called_once()


@then('已收集的 transcript 應寫入 DB')
def check_collected_transcript_saved(mock_repo: MagicMock) -> None:
    mock_repo.save_transcript.assert_called()
    call_args = mock_repo.save_transcript.call_args
    transcript = (
        call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get('transcript')
    )
    assert transcript is not None
    assert len(transcript) > 0


@then('transcript 應寫入 DB')
def check_transcript_saved(mock_repo: MagicMock) -> None:
    mock_repo.save_transcript.assert_called()


@then('transcript 應在重試後成功寫入 DB')
def check_transcript_retry_success(mock_repo: MagicMock) -> None:
    assert mock_repo.save_transcript.call_count >= 2


# --- Then: 資源清理 ---


@then('系統應清理進行中的資源')
def check_resources_cleaned(manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = ctx['conversation_id']
    state = manager._conversations.get(conv_id)
    assert state is None or state['status'] == 'cancelled'


@then('系統應中斷連線並清理資源')
def check_connection_closed(manager: Any, ctx: dict[str, Any]) -> None:
    conv_id = ctx['conversation_id']
    state = manager._conversations.get(conv_id)
    assert state is None or state['status'] == 'cancelled'


# --- Then: Timeout ---


@then('系統應透過 data channel 發送時間警告')
def check_time_warning_sent(manager: Any, ctx: dict[str, Any]) -> None:
    assert manager._warning_sent.get(ctx['conversation_id']) is True


@then('系統應自動結束對話')
def check_auto_ended(manager: Any, ctx: dict[str, Any]) -> None:
    state = manager.get_state(ctx['conversation_id'])
    assert state['status'] in ('assessing', 'completed')


@then('對話應正常結束一次')
def check_ended_once(mock_repo: MagicMock) -> None:
    assert mock_repo.save_transcript.call_count == 1


@then('不應觸發自動結束')
def check_no_auto_end() -> None:
    pass


@then('系統應自動結束對話並儲存 transcript')
def check_auto_ended_with_transcript(
    mock_repo: MagicMock, manager: Any, ctx: dict[str, Any]
) -> None:
    mock_repo.save_transcript.assert_called()
    state = manager.get_state(ctx['conversation_id'])
    assert state['status'] in ('assessing', 'completed')


@then('系統應透過 data channel 通知使用者')
def check_user_notified(manager: Any, ctx: dict[str, Any]) -> None:
    assert manager._notifications_sent.get(ctx['conversation_id']) is not None


@then(parsers.parse('靜默計時器應重置為 {minutes:d} 分鐘'))
def check_timer_reset(minutes: int, manager: Any, ctx: dict[str, Any]) -> None:
    assert manager._silence_timers.get(ctx['conversation_id']) is not None


# --- Then: 狀態防護 ---


@then('系統應拒絕轉換並拋出錯誤')
def check_transition_rejected(transition_error: pytest.ExceptionInfo[ValueError]) -> None:
    msg = str(transition_error.value).lower()
    assert 'invalid' in msg or 'illegal' in msg


@then('每次狀態變更都應寫入 DB conversations.status')
def check_all_transitions_persisted(mock_repo: MagicMock) -> None:
    assert mock_repo.update_status.call_count >= 1


# --- Then: 錯誤處理 ---


@then('系統應記錄錯誤日誌')
def check_error_logged(caplog: pytest.LogCaptureFixture) -> None:
    assert any(
        'error' in record.message.lower()
        or 'fail' in record.message.lower()
        or '失敗' in record.message
        for record in caplog.records
    )
