-- 模型配置表（可選模型 + 定價）
CREATE TABLE IF NOT EXISTS model_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL,                    -- 'claude' | 'gemini'
    model_id TEXT NOT NULL UNIQUE,             -- e.g. 'claude-sonnet-4-20250514'
    display_name TEXT NOT NULL,                -- e.g. 'Claude Sonnet 4'
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    pricing JSONB NOT NULL,                    -- 定價欄位，格式依 provider 不同
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_config_provider
    ON model_config (provider);

CREATE INDEX IF NOT EXISTS idx_model_config_active
    ON model_config (provider, is_active) WHERE is_active = TRUE;
