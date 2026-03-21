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
def mock_gemini_client() -> MagicMock:
    client = MagicMock()
    session = AsyncMock()

    async def _fake_stream(**kwargs: Any) -> Any:
        await asyncio.sleep(0)
        return
        yield

    session.start_stream = MagicMock(side_effect=_fake_stream)
    session.close = AsyncMock()

    connect_cm = AsyncMock()
    connect_cm.__aenter__ = AsyncMock(return_value=session)
    connect_cm.__aexit__ = AsyncMock(return_value=False)
    client.aio.live.connect = MagicMock(return_value=connect_cm)
    client._session = session
    return client


@pytest.fixture
def mock_on_disconnect() -> MagicMock:
    return MagicMock()


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


@pytest.fixture
def handler(mock_on_disconnect: MagicMock) -> Any:
    from persochattai.conversation.gemini_handler import GeminiHandler

    return GeminiHandler(on_disconnect=mock_on_disconnect)


# --- Given: Handler 狀態 ---


@given('GeminiHandler 已建立且 session 就緒')
def handler_ready(handler: Any, mock_gemini_client: MagicMock) -> None:
    handler._gemini_client = mock_gemini_client
    handler._session_ready = True


@given('output queue 中有音訊資料')
def output_has_audio(handler: Any) -> None:
    audio_frame = (24000, np.zeros(480, dtype=np.int16))
    handler.output_queue.put_nowait(audio_frame)


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
def handler_with_transcript(handler: Any, mock_gemini_client: MagicMock) -> None:
    handler._gemini_client = mock_gemini_client
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


@given('GeminiHandler 已建立且有合法的 Gemini client')
def handler_with_client(handler: Any, mock_gemini_client: MagicMock) -> None:
    handler._gemini_client = mock_gemini_client


@given('GeminiHandler 已建立且 Gemini client 的 connect 會失敗')
def handler_with_failing_client(handler: Any, mock_gemini_client: MagicMock) -> None:
    connect_cm = AsyncMock()
    connect_cm.__aenter__ = AsyncMock(side_effect=ConnectionError('auth failed'))
    connect_cm.__aexit__ = AsyncMock(return_value=False)
    mock_gemini_client.aio.live.connect = MagicMock(return_value=connect_cm)
    handler._gemini_client = mock_gemini_client


# --- When: 音訊串流 ---


@when('收到使用者音訊 frame')
def receive_audio(handler: Any) -> None:
    audio_frame = (16000, np.random.randint(-32768, 32767, size=480, dtype=np.int16))
    _run(handler.receive(audio_frame))


@when('呼叫 emit', target_fixture='emit_result')
def call_emit(handler: Any) -> Any:
    return _run(handler.emit())


@when('收到空的音訊 frame')
def receive_empty_audio(handler: Any) -> None:
    audio_frame = (16000, np.array([], dtype=np.int16))
    _run(handler.receive(audio_frame))


# --- When: 生命週期 ---


@when('呼叫 start_up')
def call_start_up(handler: Any) -> None:
    with contextlib.suppress(Exception):
        _run(handler.start_up())


@when('呼叫 shutdown')
def call_shutdown(handler: Any) -> None:
    handler.shutdown()


@when('連線已關閉且 output queue 為空', target_fixture='emit_after_close')
def emit_after_close(handler: Any) -> Any:
    handler.shutdown()
    return _run(handler.emit())


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


# --- When: Session 配置 ---


@when('建立 Gemini session 配置', target_fixture='session_config')
def create_session_config(ctx: dict[str, Any]) -> Any:
    from persochattai.conversation.gemini_handler import GeminiHandler

    return GeminiHandler.build_live_connect_config(
        system_instruction=ctx['system_instruction'],
    )


# --- When: 錯誤 ---


@when('stream loop 發生例外')
def stream_loop_error(handler: Any) -> None:
    _run(handler._handle_stream_error(ConnectionError('stream closed')))


# --- When: 防護 ---


@when('receiver loop 收到殘留的 transcript 事件')
def receive_stale_event(handler: Any) -> None:
    handler._handle_transcript_event('input_transcription', 'stale text', finished=True)


# --- Then: 音訊串流 ---


@then('音訊應被放入 input queue')
def check_audio_in_queue(handler: Any) -> None:
    assert not handler.input_queue.empty()


@then('應回傳音訊 frame 格式為 (sample_rate, ndarray)')
def check_emit_returns_audio(emit_result: Any) -> None:
    assert emit_result is not None
    sample_rate, audio_data = emit_result
    assert sample_rate > 0
    assert isinstance(audio_data, np.ndarray)


@then('input queue 應為空')
def check_input_queue_empty(handler: Any) -> None:
    assert handler.input_queue.empty()


# --- Then: 生命週期 ---


@then('應透過 client.aio.live.connect 建立 session')
def check_connect_called(mock_gemini_client: MagicMock) -> None:
    mock_gemini_client.aio.live.connect.assert_called_once()


@then('應啟動 stream loop 處理音訊')
def check_stream_started(mock_gemini_client: MagicMock) -> None:
    session = mock_gemini_client._session
    session.start_stream.assert_called_once()


@then('quit event 應被設定')
def check_quit_set(handler: Any) -> None:
    assert handler.quit.is_set()


@then('stream generator 應停止 yield')
def check_stream_stopped(handler: Any) -> None:
    assert handler.quit.is_set()


@then('emit 應回傳 None')
def check_emit_none(emit_after_close: Any) -> None:
    assert emit_after_close is None


# --- Then: Copy ---


@then('應建立新的 GeminiHandler 實例')
def check_new_instance(copied_handler: Any, handler: Any) -> None:
    assert copied_handler is not handler


@then('新實例應有獨立的 transcript buffer')
def check_independent_buffer(copied_handler: Any, handler: Any) -> None:
    assert copied_handler._transcript is not handler._transcript


@then('新實例應有獨立的 input queue 和 output queue')
def check_independent_queues(copied_handler: Any, handler: Any) -> None:
    assert copied_handler.input_queue is not handler.input_queue
    assert copied_handler.output_queue is not handler.output_queue


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


@then(parsers.parse('config 的 system_instruction 應為 "{instruction}"'))
def check_system_instruction(instruction: str, session_config: Any) -> None:
    si = session_config.system_instruction
    text = si if isinstance(si, str) else str(si)
    assert instruction in text


@then('config 的 response_modalities 應包含 AUDIO')
def check_response_modalities(session_config: Any) -> None:
    assert any('AUDIO' in str(m) for m in session_config.response_modalities)


@then('config 應啟用 input_audio_transcription')
def check_input_transcription_enabled(session_config: Any) -> None:
    assert session_config.input_audio_transcription is not None


@then('config 應啟用 output_audio_transcription')
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


# --- Then: 防護 ---


@then('不應拋出例外')
def check_no_exception() -> None:
    # 執行到這裡代表 When 步驟沒有拋出例外
    pass


@then('不應寫入 transcript buffer')
def check_no_transcript_written(handler: Any) -> None:
    assert len(handler._transcript) == 0
