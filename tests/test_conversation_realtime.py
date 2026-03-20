"""Gemini Realtime 測試。"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios('features/gemini_realtime.feature')


def _run(coro: Any) -> Any:
    """在 sync step 中執行 async coroutine。"""
    return asyncio.run(coro)


# --- Fixtures ---


@pytest.fixture
def mock_gemini_session() -> MagicMock:
    session = MagicMock()
    session.send = AsyncMock()
    session.receive = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_on_disconnect() -> MagicMock:
    return MagicMock()


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


@pytest.fixture
def handler(mock_gemini_session: MagicMock, mock_on_disconnect: MagicMock) -> Any:
    from persochattai.conversation.gemini_handler import GeminiHandler

    return GeminiHandler(
        gemini_session=mock_gemini_session,
        on_disconnect=mock_on_disconnect,
    )


# --- Given: Handler 狀態 ---


@given('GeminiHandler 已建立且 Gemini session 就緒')
def handler_ready(handler: Any) -> None:
    handler._session_ready = True


@given('Gemini 回應佇列中有音訊資料')
def gemini_has_audio(handler: Any) -> None:
    audio_frame = (48000, np.zeros(480, dtype=np.int16))
    handler._audio_output_queue.put_nowait(audio_frame)


@given('GeminiHandler 已建立')
def handler_created(handler: Any) -> None:
    pass


@given('兩個獨立的 GeminiHandler 實例', target_fixture='handler_pair')
def two_handlers(handler: Any) -> tuple[Any, Any]:
    handler_a = handler
    handler_b = handler.copy()
    return (handler_a, handler_b)


@given(parsers.parse('scenario_designer 產出 system instruction "{instruction}"'))
def designer_produced_instruction(instruction: str, ctx: dict[str, Any]) -> None:
    ctx['system_instruction'] = instruction


@given('GeminiHandler 已建立且已收集 2 筆 transcript')
def handler_with_transcript(handler: Any) -> None:
    handler._session_ready = True
    handler._transcript.append(
        {'role': 'user', 'text': 'Hello', 'timestamp': '2026-03-20T10:01:00'}
    )
    handler._transcript.append(
        {'role': 'model', 'text': 'Hi there', 'timestamp': '2026-03-20T10:01:05'}
    )


@given('scenario_designer 已產出 system instruction')
def designer_has_instruction(ctx: dict[str, Any]) -> None:
    ctx['system_instruction'] = 'You are a hotel receptionist.'


@given('GeminiHandler 已建立但 start_up 尚未完成')
def handler_not_ready(handler: Any) -> None:
    handler._session_ready = False


@given('GeminiHandler 已建立但對話已結束')
def handler_ended(handler: Any) -> None:
    handler._session_ready = False
    handler._ended = True


# --- When: 音訊串流 ---


@when('收到使用者音訊 frame')
def receive_audio(handler: Any) -> None:
    audio_frame = (48000, np.random.randint(-32768, 32767, size=480, dtype=np.int16))
    _run(handler.receive(audio_frame))


@when('呼叫 emit', target_fixture='emit_result')
def call_emit(handler: Any) -> Any:
    return _run(handler.emit())


@when('收到空的音訊 frame')
def receive_empty_audio(handler: Any) -> None:
    audio_frame = (48000, np.array([], dtype=np.int16))
    _run(handler.receive(audio_frame))


# --- When: Copy ---


@when('呼叫 copy', target_fixture='copied_handler')
def call_copy(handler: Any) -> Any:
    return handler.copy()


# --- When: Transcript 收集 ---


@when('實例 A 收集到一筆 transcript')
def instance_a_collects(handler_pair: tuple[Any, Any]) -> None:
    handler_a, _ = handler_pair
    handler_a._transcript.append(
        {'role': 'user', 'text': 'Hello', 'timestamp': '2026-03-20T10:01:00'}
    )


@when(
    parsers.parse('Gemini 送出 input_transcription 事件且 finished 為 True 內容為 "{text}"'),
)
def receive_input_transcript_finished(text: str, handler: Any) -> None:
    handler._handle_transcript_event('input_transcription', text, finished=True)


@when(
    parsers.parse('Gemini 送出 output_transcription 事件且 finished 為 True 內容為 "{text}"'),
)
def receive_output_transcript_finished(text: str, handler: Any) -> None:
    handler._handle_transcript_event('output_transcription', text, finished=True)


@when(
    parsers.parse('Gemini 送出 input_transcription 事件且 finished 為 False 內容為 "{text}"'),
)
def receive_input_transcript_partial(text: str, handler: Any) -> None:
    handler._handle_transcript_event('input_transcription', text, finished=False)


@when('依序收到以下完成的 transcript 事件:')
def receive_multiple_transcripts(datatable: list[list[str]], handler: Any) -> None:
    for row in datatable[1:]:
        role, text = row[0], row[1]
        event_type = 'input_transcription' if role == 'user' else 'output_transcription'
        handler._handle_transcript_event(event_type, text, finished=True)


# --- When: Session ---


@when('建立 Gemini Live session', target_fixture='session_config')
def create_session(ctx: dict[str, Any]) -> Any:
    from persochattai.conversation.gemini_handler import GeminiHandler

    return GeminiHandler.build_session_config(
        system_instruction=ctx['system_instruction'],
    )


# --- When: 錯誤 ---


@when('Gemini session 的 receiver loop 發生例外')
def receiver_loop_error(handler: Any) -> None:
    _run(handler._handle_receiver_error(ConnectionError('stream closed')))


@when('Gemini Live session 建立時拋出例外')
def session_creation_error(handler: Any, mock_gemini_session: MagicMock) -> None:
    mock_gemini_session.send.side_effect = ConnectionError('failed to connect')
    with contextlib.suppress(ConnectionError):
        _run(handler.start_up())


@when('send_realtime_input 拋出例外')
def send_input_error(handler: Any, mock_gemini_session: MagicMock) -> None:
    mock_gemini_session.send.side_effect = RuntimeError('send failed')
    audio_frame = (48000, np.random.randint(-32768, 32767, size=480, dtype=np.int16))
    _run(handler.receive(audio_frame))


# --- When: 防護 ---


@when('receiver loop 收到殘留的 transcript 事件')
def receive_stale_event(handler: Any) -> None:
    handler._handle_transcript_event('input_transcription', 'stale text', finished=True)


# --- Then: 音訊串流 ---


@then('音訊應透過 send_realtime_input 傳送至 Gemini')
def check_audio_sent(mock_gemini_session: MagicMock) -> None:
    mock_gemini_session.send.assert_called()


@then('應回傳 Gemini 的音訊 frame')
def check_emit_returns_audio(emit_result: Any) -> None:
    assert emit_result is not None
    sample_rate, _audio_data = emit_result
    assert sample_rate > 0


@then('不應呼叫 send_realtime_input')
def check_no_send(mock_gemini_session: MagicMock) -> None:
    mock_gemini_session.send.assert_not_called()


# --- Then: Copy ---


@then('應建立新的 GeminiHandler 實例')
def check_new_instance(copied_handler: Any, handler: Any) -> None:
    assert copied_handler is not handler


@then('新實例應有獨立的 transcript buffer')
def check_independent_buffer(copied_handler: Any, handler: Any) -> None:
    assert copied_handler._transcript is not handler._transcript


# --- Then: Transcript ---


@then(parsers.parse('實例 B 的 transcript buffer 應為空'))
def check_instance_b_empty(handler_pair: tuple[Any, Any]) -> None:
    _, handler_b = handler_pair
    assert len(handler_b._transcript) == 0


@then(
    parsers.parse('transcript buffer 應包含一筆 role 為 "{role}" text 為 "{text}" 的記錄'),
)
def check_single_transcript(role: str, text: str, handler: Any) -> None:
    matching = [t for t in handler._transcript if t['role'] == role and t['text'] == text]
    assert len(matching) == 1


@then('該記錄應包含 timestamp')
def check_has_timestamp(handler: Any) -> None:
    for entry in handler._transcript:
        assert 'timestamp' in entry
        assert entry['timestamp'] is not None


@then('transcript buffer 應為空')
def check_buffer_empty(handler: Any) -> None:
    assert len(handler._transcript) == 0


@then(parsers.parse('transcript buffer 應包含 {count:d} 筆記錄且順序正確'))
def check_transcript_count_and_order(count: int, handler: Any) -> None:
    assert len(handler._transcript) == count
    timestamps = [t['timestamp'] for t in handler._transcript]
    assert timestamps == sorted(timestamps)


# --- Then: Session 配置 ---


@then(parsers.parse('session 的 system_instruction 應為 "{instruction}"'))
def check_system_instruction(instruction: str, session_config: Any) -> None:
    assert session_config.system_instruction == instruction


@then('session 的 response_modalities 應為 AUDIO')
def check_response_modalities(session_config: Any) -> None:
    assert 'AUDIO' in session_config.response_modalities


@then('session 應啟用 input_audio_transcription')
def check_input_transcription_enabled(session_config: Any) -> None:
    assert session_config.input_audio_transcription is not None


@then('session 應啟用 output_audio_transcription')
def check_output_transcription_enabled(session_config: Any) -> None:
    assert session_config.output_audio_transcription is not None


# --- Then: 錯誤處理 ---


@then(parsers.parse('已收集的 {count:d} 筆 transcript 應被保留'))
def check_transcript_preserved(count: int, handler: Any) -> None:
    assert len(handler._transcript) == count


@then('應透過回呼通知 ConversationManager')
def check_callback_called(mock_on_disconnect: MagicMock) -> None:
    mock_on_disconnect.assert_called()


@then('應透過回呼通知 ConversationManager 設定狀態為 failed')
def check_callback_failed(mock_on_disconnect: MagicMock) -> None:
    mock_on_disconnect.assert_called()
    call_kwargs = mock_on_disconnect.call_args.kwargs
    assert call_kwargs.get('status') == 'failed'


@then('應記錄錯誤但不中斷 handler')
def check_error_logged_handler_alive(handler: Any) -> None:
    assert handler._session_ready is True


# --- Then: 防護 ---


@then('不應拋出例外')
def check_no_exception() -> None:
    # 執行到這裡代表 When 步驟沒有拋出例外
    pass


@then('音訊應被忽略')
def check_audio_ignored(mock_gemini_session: MagicMock) -> None:
    mock_gemini_session.send.assert_not_called()


@then('不應寫入 transcript buffer')
def check_no_transcript_written(handler: Any) -> None:
    assert len(handler._transcript) == 0
