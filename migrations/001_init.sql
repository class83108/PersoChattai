-- PersoChattai 初始 schema
-- 使用 CREATE TABLE IF NOT EXISTS 確保可重複執行

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_name TEXT NOT NULL,
    current_level TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    dialogue_snippets JSONB NOT NULL DEFAULT '[]'::jsonb,
    difficulty_level TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT,
    system_instruction TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    transcript JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'preparing'
);

CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    -- 量化指標
    mtld DOUBLE PRECISION,
    vocd_d DOUBLE PRECISION,
    k1_ratio DOUBLE PRECISION,
    k2_ratio DOUBLE PRECISION,
    awl_ratio DOUBLE PRECISION,
    new_words_count INTEGER,
    new_words TEXT[] NOT NULL DEFAULT '{}',
    avg_sentence_length DOUBLE PRECISION,
    conjunction_ratio DOUBLE PRECISION,
    self_correction_count INTEGER,
    subordinate_clause_ratio DOUBLE PRECISION,
    tense_diversity INTEGER,
    grammar_error_rate DOUBLE PRECISION,
    -- 質性分析
    cefr_level TEXT,
    lexical_assessment TEXT,
    fluency_assessment TEXT,
    grammar_assessment TEXT,
    suggestions TEXT[] NOT NULL DEFAULT '{}',
    raw_analysis JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_vocabulary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    word TEXT NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    first_seen_conversation_id UUID REFERENCES conversations(id),
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, word)
);

CREATE TABLE IF NOT EXISTS user_level_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    snapshot_date DATE NOT NULL,
    cefr_level TEXT,
    avg_mtld DOUBLE PRECISION,
    avg_vocd_d DOUBLE PRECISION,
    vocabulary_size INTEGER,
    strengths TEXT[] NOT NULL DEFAULT '{}',
    weaknesses TEXT[] NOT NULL DEFAULT '{}',
    conversation_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
