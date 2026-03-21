"""Assessment Service — 評估 pipeline。"""

from __future__ import annotations

import logging
from typing import Any

from persochattai.assessment.nlp import NlpAnalyzer
from persochattai.assessment.schemas import (
    AssessmentAgentProtocol,
    AssessmentRepositoryProtocol,
    NlpMetrics,
    SnapshotRepositoryProtocol,
    VocabularyRepositoryProtocol,
)

logger = logging.getLogger(__name__)

CEFR_LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
_SNAPSHOT_INTERVAL = 5


class AssessmentService:
    def __init__(
        self,
        assessment_repo: AssessmentRepositoryProtocol,
        vocabulary_repo: VocabularyRepositoryProtocol,
        snapshot_repo: SnapshotRepositoryProtocol,
        agent: AssessmentAgentProtocol,
    ) -> None:
        self._assessment_repo = assessment_repo
        self._vocabulary_repo = vocabulary_repo
        self._snapshot_repo = snapshot_repo
        self._agent = agent
        self._nlp = NlpAnalyzer()

    async def evaluate(
        self, conversation_id: str, user_id: str, transcript: str
    ) -> dict[str, Any] | None:
        if not transcript.strip():
            return None

        # Step 1: NLP metrics
        metrics = self._nlp.analyze(transcript)

        # Step 2: Claude qualitative analysis
        qualitative = await self._run_qualitative_analysis(transcript, metrics)

        # Step 3: Build assessment data
        data = self._build_assessment_data(conversation_id, user_id, metrics, qualitative)

        # Step 4: Save assessment
        result = await self._assessment_repo.create(data)

        # Step 5: Update vocabulary
        new_words = (qualitative or {}).get('new_words', [])
        if new_words:
            await self._vocabulary_repo.upsert_words(
                user_id=user_id,
                words=new_words,
                conversation_id=conversation_id,
            )

        # Step 6: Check snapshot trigger
        count = await self._assessment_repo.count_by_user(user_id)
        if count > 0 and count % _SNAPSHOT_INTERVAL == 0:
            await self._create_snapshot(user_id, metrics, qualitative)

        return result

    async def get_user_history(self, user_id: str) -> dict[str, Any]:
        snapshot = await self._snapshot_repo.get_latest(user_id)
        assessments = await self._assessment_repo.list_by_user(user_id, limit=5, offset=0)
        vocab_stats = await self._vocabulary_repo.get_vocabulary_stats(user_id)
        return {
            'snapshot': snapshot,
            'recent_assessments': assessments,
            'vocabulary_stats': vocab_stats,
        }

    async def _run_qualitative_analysis(
        self, transcript: str, metrics: NlpMetrics
    ) -> dict[str, Any] | None:
        try:
            result = await self._agent.run(transcript)
            if not isinstance(result, dict):
                logger.error('Claude Agent 回傳非預期格式')
                return None
            return result
        except Exception:
            logger.error('Claude Agent 評估失敗: %s', transcript[:50])
            return None

    def _build_assessment_data(
        self,
        conversation_id: str,
        user_id: str,
        metrics: NlpMetrics,
        qualitative: dict[str, Any] | None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'mtld': metrics.mtld,
            'vocd_d': metrics.vocd_d,
            'k1_ratio': metrics.k1_ratio,
            'k2_ratio': metrics.k2_ratio,
            'awl_ratio': metrics.awl_ratio,
            'avg_sentence_length': metrics.avg_sentence_length,
            'conjunction_ratio': metrics.conjunction_ratio,
            'self_correction_count': metrics.self_correction_count,
            'subordinate_clause_ratio': metrics.subordinate_clause_ratio,
            'tense_diversity': metrics.tense_diversity,
            'grammar_error_count': metrics.grammar_error_count,
        }
        if qualitative:
            data.update(
                {
                    'cefr_level': qualitative.get('cefr_level'),
                    'lexical_assessment': qualitative.get('lexical_assessment'),
                    'fluency_assessment': qualitative.get('fluency_assessment'),
                    'grammar_assessment': qualitative.get('grammar_assessment'),
                    'suggestions': qualitative.get('suggestions', []),
                    'new_words': qualitative.get('new_words', []),
                }
            )
        else:
            data.update(
                {
                    'cefr_level': None,
                    'lexical_assessment': None,
                    'fluency_assessment': None,
                    'grammar_assessment': None,
                    'suggestions': [],
                    'new_words': [],
                }
            )
        return data

    async def _create_snapshot(
        self,
        user_id: str,
        metrics: NlpMetrics,
        qualitative: dict[str, Any] | None,
    ) -> None:
        vocab_stats = await self._vocabulary_repo.get_vocabulary_stats(user_id)
        await self._snapshot_repo.create_snapshot(
            user_id=user_id,
            data={
                'cefr_level': (qualitative or {}).get('cefr_level'),
                'avg_mtld': metrics.mtld,
                'avg_vocd_d': metrics.vocd_d,
                'vocabulary_size': vocab_stats.get('total_words', 0),
            },
        )
