"""DB 管理 — 委派至 database.engine。

保留此模組以維持 import 相容性，實際邏輯在 database.engine。
"""

from persochattai.database.engine import (
    dispose_engine,
    get_session,
    get_session_factory,
    init_engine,
    run_migrations,
)

__all__ = ['dispose_engine', 'get_session', 'get_session_factory', 'init_engine', 'run_migrations']
