"""Assessment DB repository — SQLAlchemy 實作。"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from persochattai.database.tables import AssessmentTable


class AssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        assessment_id = data.get('id', str(uuid.uuid4()))
        row = AssessmentTable(
            id=assessment_id,
            conversation_id=data['conversation_id'],
            user_id=data['user_id'],
            mtld=data.get('mtld'),
            vocd_d=data.get('vocd_d'),
            k1_ratio=data.get('k1_ratio'),
            k2_ratio=data.get('k2_ratio'),
            awl_ratio=data.get('awl_ratio'),
            new_words_count=len(data.get('new_words', [])),
            new_words=data.get('new_words', []),
            avg_sentence_length=data.get('avg_sentence_length'),
            conjunction_ratio=data.get('conjunction_ratio'),
            self_correction_count=data.get('self_correction_count'),
            subordinate_clause_ratio=data.get('subordinate_clause_ratio'),
            tense_diversity=data.get('tense_diversity'),
            grammar_error_rate=data.get('grammar_error_count'),
            cefr_level=data.get('cefr_level'),
            lexical_assessment=data.get('lexical_assessment'),
            fluency_assessment=data.get('fluency_assessment'),
            grammar_assessment=data.get('grammar_assessment'),
            suggestions=data.get('suggestions', []),
            raw_analysis=data.get('raw_analysis'),
        )
        self._session.add(row)
        await self._session.flush()
        return _row_to_dict(row)

    async def get_by_id(self, assessment_id: str) -> dict[str, Any] | None:
        stmt = select(AssessmentTable).where(AssessmentTable.id == assessment_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_dict(row) if row else None

    async def list_by_user(
        self, user_id: str, *, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        stmt = (
            select(AssessmentTable)
            .where(AssessmentTable.user_id == user_id)
            .order_by(AssessmentTable.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_row_to_dict(row) for row in result.scalars().all()]

    async def count_by_user(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(AssessmentTable)
            .where(AssessmentTable.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)


def _row_to_dict(row: AssessmentTable) -> dict[str, Any]:
    return {
        'id': row.id,
        'conversation_id': row.conversation_id,
        'user_id': row.user_id,
        'mtld': row.mtld,
        'vocd_d': row.vocd_d,
        'k1_ratio': row.k1_ratio,
        'k2_ratio': row.k2_ratio,
        'awl_ratio': row.awl_ratio,
        'new_words_count': row.new_words_count,
        'new_words': row.new_words,
        'avg_sentence_length': row.avg_sentence_length,
        'conjunction_ratio': row.conjunction_ratio,
        'self_correction_count': row.self_correction_count,
        'subordinate_clause_ratio': row.subordinate_clause_ratio,
        'tense_diversity': row.tense_diversity,
        'grammar_error_rate': row.grammar_error_rate,
        'cefr_level': row.cefr_level,
        'lexical_assessment': row.lexical_assessment,
        'fluency_assessment': row.fluency_assessment,
        'grammar_assessment': row.grammar_assessment,
        'suggestions': row.suggestions,
        'raw_analysis': row.raw_analysis,
        'created_at': row.created_at,
    }
