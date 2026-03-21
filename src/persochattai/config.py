"""應用程式環境配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        msg = f'必要環境變數 {key} 未設定，請檢查 .env 檔案'
        raise ValueError(msg)
    return value


@dataclass(frozen=True)
class Settings:
    db_url: str
    anthropic_api_key: str
    gemini_api_key: str
    debug: bool = False
    claude_model: str = 'claude-sonnet-4-20250514'
    gemini_model: str = 'gemini-2.0-flash'

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            db_url=_require_env('DB_URL'),
            anthropic_api_key=_require_env('ANTHROPIC_API_KEY'),
            gemini_api_key=_require_env('GEMINI_API_KEY'),
            debug=os.environ.get('DEBUG', 'false').lower() == 'true',
            claude_model=os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
            gemini_model=os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash'),
        )
