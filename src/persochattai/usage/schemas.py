"""Usage 模組的資料結構與 Protocol 定義。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

from agent_core.usage_monitor import UsageRecord

AudioDirection = Literal['input', 'output']

# Gemini Live API 音訊定價（USD per second）— 舊格式，保留供向後相容
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

# Token-based fallback 定價（DB 無資料時使用）
FALLBACK_GEMINI_PRICING: dict[str, float] = {
    'text_input': 0.10,
    'audio_input': 0.70,
    'output': 0.40,
    'tokens_per_sec': 25,
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


@dataclass
class ModelConfig:
    """模型配置（對應 model_config DB table）。"""

    provider: str
    model_id: str
    display_name: str
    is_active: bool
    pricing: dict[str, Any]
    id: str | None = field(default=None)
    created_at: datetime | None = field(default=None)
    updated_at: datetime | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'provider': self.provider,
            'model_id': self.model_id,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'pricing': self.pricing,
        }


@runtime_checkable
class UsageRepositoryProtocol(Protocol):
    async def save_token_record(self, record: UsageRecord, *, model: str) -> None: ...
    async def save_audio_record(self, record: GeminiAudioRecord) -> None: ...
    async def load_token_records(self, *, days: int = 30) -> list[UsageRecord]: ...
    async def load_audio_records(self, *, days: int = 30) -> list[GeminiAudioRecord]: ...


@runtime_checkable
class ModelConfigRepositoryProtocol(Protocol):
    async def list_models(self, *, provider: str | None = None) -> list[ModelConfig]: ...
    async def get_active_model(self, provider: str) -> ModelConfig | None: ...
    async def set_active_model(self, *, provider: str, model_id: str) -> None: ...
    async def create_model(self, model: ModelConfig) -> ModelConfig: ...
    async def update_model(self, model_id: str, updates: dict[str, Any]) -> ModelConfig: ...
    async def delete_model(self, model_id: str) -> None: ...
    async def get_model(self, model_id: str) -> ModelConfig | None: ...
    async def seed_defaults(self) -> None: ...
