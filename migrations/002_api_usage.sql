-- API 使用量紀錄表（token + Gemini 音訊共用）
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usage_type TEXT NOT NULL,              -- 'token' | 'audio'
    model TEXT,
    -- token 紀錄欄位
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_creation_input_tokens INTEGER,
    cache_read_input_tokens INTEGER,
    -- audio 紀錄欄位
    audio_duration_sec DOUBLE PRECISION,
    direction TEXT,                         -- 'input' | 'output'
    -- 共用
    cost_usd DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_type_created
    ON api_usage (usage_type, created_at);
