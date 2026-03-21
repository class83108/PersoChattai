"""Usage 模組的資料結構與 Protocol 定義。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

from agent_core.usage_monitor import UsageRecord

AudioDirection = Literal['input', 'output']

# Gemini Live API 音訊定價（USD per second）
GEMINI_AUDIO_PRICING: dict[str, dict[str, float]] = {
    'gemini-2.0-flash': {
        'input_per_second': 0.0001,
        'output_per_second': 0.0002,
    },
}

DEFAULT_GEMINI_AUDIO_PRICING: dict[str, float] = {
    'input_per_second': 0.0001,
    'output_per_second': 0.0002,
}


@dataclass
class GeminiAudioRecord:
    """單次 Gemini Live API 音訊用量紀錄。"""

    timestamp: datetime
    audio_duration_sec: float
    direction: AudioDirection
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'audio_duration_sec': self.audio_duration_sec,
            'direction': self.direction,
            'model': self.model,
        }


@runtime_checkable
class UsageRepositoryProtocol(Protocol):
    async def save_token_record(self, record: UsageRecord, *, model: str) -> None: ...
    async def save_audio_record(self, record: GeminiAudioRecord) -> None: ...
    async def load_token_records(self, *, days: int = 30) -> list[UsageRecord]: ...
    async def load_audio_records(self, *, days: int = 30) -> list[GeminiAudioRecord]: ...
