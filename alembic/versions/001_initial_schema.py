"""Initial schema — 等價於 migrations/001~003 合併。

Revision ID: 001
Revises:
Create Date: 2026-03-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('current_level', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        'cards',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('keywords', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('dialogue_snippets', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('difficulty_level', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        'idx_cards_source_url_unique',
        'cards',
        ['source_url'],
        unique=True,
        postgresql_where=sa.text('source_url IS NOT NULL'),
    )

    op.create_table(
        'conversations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column(
            'user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False
        ),
        sa.Column('conversation_type', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_ref', sa.Text(), nullable=True),
        sa.Column('system_instruction', sa.Text(), nullable=True),
        sa.Column(
            'started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transcript', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('status', sa.Text(), server_default="'preparing'", nullable=False),
    )

    op.create_table(
        'assessments',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column(
            'conversation_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('conversations.id'),
            nullable=False,
        ),
        sa.Column(
            'user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False
        ),
        sa.Column('mtld', sa.Float(), nullable=True),
        sa.Column('vocd_d', sa.Float(), nullable=True),
        sa.Column('k1_ratio', sa.Float(), nullable=True),
        sa.Column('k2_ratio', sa.Float(), nullable=True),
        sa.Column('awl_ratio', sa.Float(), nullable=True),
        sa.Column('new_words_count', sa.Integer(), nullable=True),
        sa.Column('new_words', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('avg_sentence_length', sa.Float(), nullable=True),
        sa.Column('conjunction_ratio', sa.Float(), nullable=True),
        sa.Column('self_correction_count', sa.Integer(), nullable=True),
        sa.Column('subordinate_clause_ratio', sa.Float(), nullable=True),
        sa.Column('tense_diversity', sa.Integer(), nullable=True),
        sa.Column('grammar_error_rate', sa.Float(), nullable=True),
        sa.Column('cefr_level', sa.Text(), nullable=True),
        sa.Column('lexical_assessment', sa.Text(), nullable=True),
        sa.Column('fluency_assessment', sa.Text(), nullable=True),
        sa.Column('grammar_assessment', sa.Text(), nullable=True),
        sa.Column('suggestions', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('raw_analysis', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        'user_vocabulary',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column(
            'user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False
        ),
        sa.Column('word', sa.Text(), nullable=False),
        sa.Column(
            'first_seen_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'first_seen_conversation_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('conversations.id'),
            nullable=True,
        ),
        sa.Column('occurrence_count', sa.Integer(), server_default='1', nullable=False),
        sa.UniqueConstraint('user_id', 'word'),
    )

    op.create_table(
        'user_level_snapshots',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column(
            'user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False
        ),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('cefr_level', sa.Text(), nullable=True),
        sa.Column('avg_mtld', sa.Float(), nullable=True),
        sa.Column('avg_vocd_d', sa.Float(), nullable=True),
        sa.Column('vocabulary_size', sa.Integer(), nullable=True),
        sa.Column('strengths', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('weaknesses', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('conversation_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        'api_usage',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column('usage_type', sa.Text(), nullable=False),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cache_creation_input_tokens', sa.Integer(), nullable=True),
        sa.Column('cache_read_input_tokens', sa.Integer(), nullable=True),
        sa.Column('audio_duration_sec', sa.Float(), nullable=True),
        sa.Column('direction', sa.Text(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index('idx_api_usage_type_created', 'api_usage', ['usage_type', 'created_at'])

    op.create_table(
        'model_config',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            primary_key=True,
        ),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('model_id', sa.Text(), nullable=False, unique=True),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('pricing', postgresql.JSONB(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index('idx_model_config_provider', 'model_config', ['provider'])
    op.create_index(
        'idx_model_config_active',
        'model_config',
        ['provider', 'is_active'],
        postgresql_where=sa.text('is_active = TRUE'),
    )


def downgrade() -> None:
    op.drop_table('model_config')
    op.drop_table('api_usage')
    op.drop_table('user_level_snapshots')
    op.drop_table('user_vocabulary')
    op.drop_table('assessments')
    op.drop_table('conversations')
    op.drop_table('cards')
    op.drop_table('users')
