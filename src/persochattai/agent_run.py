"""Agent run wrapper — 收集 stream_message 並回傳結構化結果。"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StreamableAgent(Protocol):
    def stream_message(
        self,
        content: str,
        attachments: Any = None,
        stream_id: str | None = None,
    ) -> AsyncIterator[str | dict[str, Any]]: ...


async def agent_run(agent: StreamableAgent, message: str) -> Any:
    """呼叫 agent.stream_message() 並收集結果。

    只收集 str chunks，忽略 AgentEvent（dict 類型）。
    嘗試將組合文字解析為 JSON（dict 或 list），失敗則以 {"raw": text} 回傳。
    """
    chunks: list[str] = []
    async for event in agent.stream_message(content=message):
        if isinstance(event, str):
            chunks.append(event)

    text = ''.join(chunks).strip()
    return _extract_json(text)


def _extract_json(text: str) -> Any:
    """從文字中提取 JSON。支援 dict、list、markdown code fence。"""
    if not text:
        return {'raw': ''}

    # 嘗試直接解析
    try:
        result = json.loads(text)
        if isinstance(result, (dict, list)):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # 嘗試剝離 markdown code fence
    match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(1).strip())
            if isinstance(result, (dict, list)):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return {'raw': text}
