"""App 入口點：python -m persochattai。"""

from __future__ import annotations

import uvicorn

from persochattai.config import Settings


def main() -> None:
    settings = Settings.from_env()
    uvicorn.run(
        'persochattai.app:create_app',
        factory=True,
        host='127.0.0.1',
        port=8000,
        reload=settings.debug,
    )


if __name__ == '__main__':
    main()
