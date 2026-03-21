"""FastRTC Stream 掛載。"""

from __future__ import annotations

from fastapi import FastAPI
from fastrtc import Stream

from persochattai.conversation.gemini_handler import GeminiHandler


def create_conversation_stream() -> tuple[FastAPI, Stream]:
    handler = GeminiHandler()
    stream = Stream(
        handler=handler,
        modality='audio',
        mode='send-receive',
    )
    app = FastAPI()
    stream.mount(app, path='/api/conversation/rtc')
    return app, stream


def mount_conversation_stream(app: FastAPI) -> Stream:
    handler = GeminiHandler()
    stream = Stream(
        handler=handler,
        modality='audio',
        mode='send-receive',
    )
    stream.mount(app, path='/api/conversation/rtc')
    return stream
