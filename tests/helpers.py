"""共用 test helpers。"""

from __future__ import annotations

import json
from typing import Any


class MockStreamAgent:
    """模擬 BYOA Agent 的 stream_message 行為。

    將 return_value 序列化為 JSON 並透過 async generator yield。
    可透過設定 side_effect 為 Exception 模擬錯誤。
    """

    def __init__(self, return_value: Any = None, side_effect: Exception | None = None) -> None:
        self.return_value = return_value
        self.side_effect = side_effect

    async def stream_message(
        self,
        content: str,
        attachments: Any = None,
        stream_id: str | None = None,
    ) -> Any:
        if self.side_effect is not None:
            raise self.side_effect
        text = json.dumps(self.return_value, ensure_ascii=False)
        yield text
