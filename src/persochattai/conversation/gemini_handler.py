"""GeminiHandler — 橋接 FastRTC WebRTC 音訊與 Gemini Live API。"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class GeminiSessionConfig:
    system_instruction: str
    response_modalities: list[str] = field(default_factory=lambda: ['AUDIO'])
    input_audio_transcription: dict[str, Any] | None = field(default_factory=dict)
    output_audio_transcription: dict[str, Any] | None = field(default_factory=dict)


class GeminiHandler:
    def __init__(
        self,
        *,
        gemini_session: Any | None = None,
        on_disconnect: Any | None = None,
    ) -> None:
        self._gemini_session = gemini_session
        self._on_disconnect = on_disconnect
        self._session_ready = False
        self._ended = False
        self._transcript: list[dict[str, Any]] = []
        self._audio_output_queue: asyncio.Queue[tuple[int, np.ndarray[Any, Any]]] = asyncio.Queue()

    async def receive(self, frame: tuple[int, np.ndarray[Any, Any]]) -> None:
        if not self._session_ready or self._ended or self._gemini_session is None:
            return

        _sample_rate, audio_data = frame
        if len(audio_data) == 0:
            return

        try:
            await self._gemini_session.send(audio_data.tobytes())
        except Exception:
            logger.exception('send_realtime_input 失敗')

    async def emit(self) -> tuple[int, np.ndarray[Any, Any]]:
        return await self._audio_output_queue.get()

    def copy(self) -> GeminiHandler:
        return GeminiHandler(on_disconnect=self._on_disconnect)

    async def start_up(self) -> None:
        if self._gemini_session is None:
            msg = 'Gemini session not initialized'
            raise RuntimeError(msg)
        try:
            await self._gemini_session.send(b'init')
            self._session_ready = True
        except Exception:
            if self._on_disconnect:
                self._on_disconnect(transcript=self._transcript, status='failed')
            raise

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

    async def _handle_receiver_error(self, error: Exception) -> None:
        logger.error('Gemini receiver loop 錯誤: %s', error)
        self._session_ready = False
        if self._on_disconnect:
            self._on_disconnect(transcript=self._transcript, status='failed')

    @staticmethod
    def build_session_config(system_instruction: str) -> GeminiSessionConfig:
        return GeminiSessionConfig(system_instruction=system_instruction)
