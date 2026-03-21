"""ExtendedUsageMonitor — 擴展 BYOA Core UsageMonitor。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agent_core.usage_monitor import UsageMonitor

from persochattai.usage.schemas import (
    DEFAULT_GEMINI_AUDIO_PRICING,
    FALLBACK_GEMINI_PRICING,
    GEMINI_AUDIO_PRICING,
    AudioDirection,
    GeminiAudioRecord,
    ModelConfigRepositoryProtocol,
    UsageRepositoryProtocol,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtendedUsageMonitor(UsageMonitor):
    """追蹤 token + Gemini 音訊用量，支援 DB 持久化。"""

    audio_records: list[GeminiAudioRecord] = field(default_factory=list)
    repository: UsageRepositoryProtocol | None = field(default=None, repr=False)
    model_config_repo: ModelConfigRepositoryProtocol | None = field(default=None, repr=False)
    _pricing_cache: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    async def record_audio(
        self,
        *,
        duration_sec: float,
        direction: AudioDirection,
        model: str,
    ) -> GeminiAudioRecord | None:
        if not self.enabled:
            return None

        rec = GeminiAudioRecord(
            timestamp=datetime.now(tz=UTC),
            audio_duration_sec=duration_sec,
            direction=direction,
            model=model,
        )
        self.audio_records.append(rec)

        # Cache pricing from DB if available and not yet cached
        if model not in self._pricing_cache and self.model_config_repo is not None:
            model_config = await self.model_config_repo.get_model(model)
            if model_config is not None:
                self._pricing_cache[model] = model_config.pricing

        if self.repository is not None:
            await self.repository.save_audio_record(rec)

        return rec

    async def record_and_persist(self, usage: Any) -> None:
        result = self.record(usage)
        if result is not None and self.repository is not None:
            await self.repository.save_token_record(result, model=self.model)

    def _gemini_audio_cost(self) -> float:
        total = 0.0
        for rec in self.audio_records:
            # Try token-based pricing from DB cache first
            if rec.model in self._pricing_cache:
                pricing = self._pricing_cache[rec.model]
                tokens_per_sec = pricing.get('tokens_per_sec', 25)
                audio_input_price = pricing.get('audio_input', 0.70)
                total += rec.audio_duration_sec * tokens_per_sec * audio_input_price / 1_000_000
            elif self.model_config_repo is not None:
                # DB-backed but model not in cache → fallback
                logger.warning('模型 %s 不在定價 cache 中，使用 fallback 定價', rec.model)
                tokens_per_sec = FALLBACK_GEMINI_PRICING['tokens_per_sec']
                audio_input_price = FALLBACK_GEMINI_PRICING['audio_input']
                total += rec.audio_duration_sec * tokens_per_sec * audio_input_price / 1_000_000
            else:
                # Legacy per-second pricing (no model_config_repo)
                pricing = GEMINI_AUDIO_PRICING.get(rec.model, DEFAULT_GEMINI_AUDIO_PRICING)
                key = f'{rec.direction}_per_second'
                rate = pricing.get(key)
                if rate is None:
                    logger.warning('音訊定價 key 不存在: %s (direction=%s)', key, rec.direction)
                    rate = 0.0
                total += rec.audio_duration_sec * rate
        return total

    def get_summary(self) -> dict[str, Any]:
        base = super().get_summary()

        audio_cost = self._gemini_audio_cost()
        total_duration = sum(r.audio_duration_sec for r in self.audio_records)

        base['gemini_audio'] = {
            'total_requests': len(self.audio_records),
            'total_duration_sec': round(total_duration, 2),
            'cost_usd': round(audio_cost, 6),
            'recent_records': [r.to_dict() for r in self.audio_records[-5:]],
        }

        return base

    async def load_history(self, *, days: int = 30) -> None:
        if self.repository is None:
            return
        self.records = await self.repository.load_token_records(days=days)
        self.audio_records = await self.repository.load_audio_records(days=days)
