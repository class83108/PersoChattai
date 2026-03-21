"""GeminiHandler — 橋接 FastRTC WebRTC 音訊與 Gemini Live API。"""

from __future__ import annotations

import asyncio
import base64
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import numpy as np
from fastrtc import AsyncStreamHandler, wait_for_item
from google.genai.types import (
    AudioTranscriptionConfig,
    LiveConnectConfig,
    Modality,
)

logger = logging.getLogger(__name__)


def _encode_audio(data: np.ndarray[Any, Any]) -> str:
    return base64.b64encode(data.tobytes()).decode('UTF-8')


class GeminiHandler(AsyncStreamHandler):
    def __init__(
        self,
        *,
        on_disconnect: Any | None = None,
    ) -> None:
        super().__init__(
            expected_layout='mono',
            output_sample_rate=24000,
            input_sample_rate=16000,
        )
        self._on_disconnect = on_disconnect
        self._gemini_client: Any | None = None
        self._session_ready = False
        self._ended = False
        self._transcript: list[dict[str, Any]] = []
        self.input_queue: asyncio.Queue[str] = asyncio.Queue()
        self.output_queue: asyncio.Queue[tuple[int, np.ndarray[Any, Any]]] = asyncio.Queue()
        self.quit: asyncio.Event = asyncio.Event()

    async def receive(self, frame: tuple[int, np.ndarray[Any, Any]]) -> None:
        if not self._session_ready or self._ended:
            return

        _, audio_data = frame
        if len(audio_data) == 0:
            return

        audio_data = audio_data.squeeze()
        self.input_queue.put_nowait(_encode_audio(audio_data))

    async def emit(self) -> tuple[int, np.ndarray[Any, Any]] | None:
        return await wait_for_item(self.output_queue)

    def copy(self) -> GeminiHandler:
        return GeminiHandler(on_disconnect=self._on_disconnect)

    async def start_up(self) -> None:
        if self._gemini_client is None:
            msg = 'Gemini client not initialized'
            raise RuntimeError(msg)

        config = self.build_live_connect_config(
            system_instruction=getattr(self, '_system_instruction', ''),
        )

        try:
            async with self._gemini_client.aio.live.connect(
                model='gemini-2.0-flash-exp', config=config
            ) as session:
                self._session_ready = True
                async for audio in session.start_stream(
                    stream=self._audio_stream(), mime_type='audio/pcm'
                ):
                    if audio.data:
                        array = np.frombuffer(audio.data, dtype=np.int16)
                        self.output_queue.put_nowait((self.output_sample_rate, array))
        except Exception as e:
            await self._handle_stream_error(e)

    async def _audio_stream(self) -> AsyncGenerator[str, None]:
        while not self.quit.is_set():
            try:
                audio = await asyncio.wait_for(self.input_queue.get(), 0.1)
                yield audio
            except TimeoutError:
                pass

    def shutdown(self) -> None:
        self.quit.set()

    def _handle_transcript_event(self, event_type: str, text: str, *, finished: bool) -> None:
        if self._ended:
            return
        if not finished:
            return

        role = 'user' if event_type == 'input_transcription' else 'model'
        self._transcript.append(
            {
                'role': role,
                'text': text,
                'timestamp': datetime.now(UTC).isoformat(),
            }
        )

    async def _handle_stream_error(self, error: Exception) -> None:
        logger.error('Gemini stream 錯誤: %s', error)
        self._session_ready = False
        if self._on_disconnect:
            self._on_disconnect(transcript=self._transcript, status='failed')

    @staticmethod
    def build_live_connect_config(system_instruction: str) -> LiveConnectConfig:
        return LiveConnectConfig(
            system_instruction=system_instruction,
            response_modalities=[Modality.AUDIO],
            input_audio_transcription=AudioTranscriptionConfig(),
            output_audio_transcription=AudioTranscriptionConfig(),
        )
