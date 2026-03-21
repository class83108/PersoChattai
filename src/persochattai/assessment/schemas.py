"""Assessment Service schemas。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AssessmentRepositoryProtocol(Protocol):
    async def create(self, data: dict[str, Any]) -> dict[str, Any]: ...

    async def get_by_id(self, assessment_id: str) -> dict[str, Any] | None: ...

    async def list_by_user(
        self, user_id: str, *, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]: ...

    async def count_by_user(self, user_id: str) -> int: ...


@runtime_checkable
class VocabularyRepositoryProtocol(Protocol):
    async def upsert_words(
        self, *, user_id: str, words: list[str], conversation_id: str
    ) -> None: ...

    async def get_vocabulary_stats(self, user_id: str) -> dict[str, Any]: ...


@runtime_checkable
class SnapshotRepositoryProtocol(Protocol):
    async def create_snapshot(self, *, user_id: str, data: dict[str, Any]) -> None: ...

    async def get_latest(self, user_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class AssessmentAgentProtocol(Protocol):
    async def run(self, transcript: str) -> dict[str, Any]: ...


@runtime_checkable
class AssessmentServiceProtocol(Protocol):
    async def evaluate(
        self, *, conversation_id: str, user_id: str, transcript: str
    ) -> dict[str, Any] | None: ...


@dataclass
class NlpMetrics:
    mtld: float | None = None
    vocd_d: float | None = None
    k1_ratio: float = 0.0
    k2_ratio: float = 0.0
    awl_ratio: float = 0.0
    avg_sentence_length: float = 0.0
    conjunction_ratio: float = 0.0
    self_correction_count: int = 0
    subordinate_clause_ratio: float = 0.0
    tense_diversity: int = 0
    grammar_error_count: int = 0
