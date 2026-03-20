"""ConversationManager — 對話生命週期管理。"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from persochattai.conversation.schemas import (
    VALID_TRANSITIONS,
    ConversationRepositoryProtocol,
    ConversationStatus,
    ScenarioDesigner,
)

logger = logging.getLogger(__name__)

_TRANSCRIPT_RETRY_COUNT = 3
_TRANSCRIPT_RETRY_DELAYS = [1, 2]  # seconds between retries

S = ConversationStatus


class ConversationManager:
    def __init__(
        self,
        *,
        repository: ConversationRepositoryProtocol,
        scenario_designer: ScenarioDesigner,
        gemini_client: Any,
    ) -> None:
        self._repository = repository
        self._scenario_designer = scenario_designer
        self._gemini_client = gemini_client
        self._conversations: dict[str, dict[str, Any]] = {}
        self._warning_sent: dict[str, bool] = {}
        self._silence_timers: dict[str, float] = {}
        self._notifications_sent: dict[str, dict[str, str]] = {}
        self._timeout_tasks: dict[str, asyncio.Task[None]] = {}

    async def start_conversation(
        self, user_id: str, source_type: str, source_ref: str
    ) -> dict[str, Any]:
        conv_id = str(uuid.uuid4())

        await self._repository.create(conv_id, user_id, source_type, source_ref)
        await self._repository.update_status(conv_id, S.PREPARING)

        self._conversations[conv_id] = {
            'conversation_id': conv_id,
            'user_id': user_id,
            'status': S.PREPARING,
            'source_type': source_type,
            'source_ref': source_ref,
            'transcript': [],
            'started_at': datetime.now(UTC).isoformat(),
        }

        try:
            system_instruction = await self._call_scenario_designer_with_retry(
                source_type, source_ref
            )
        except Exception:
            logger.error('scenario_designer 失敗: %s', conv_id)
            self.transition_state(conv_id, S.FAILED)
            await self._repository.update_status(conv_id, S.FAILED)
            return self._build_response(conv_id)

        self.transition_state(conv_id, S.CONNECTING)
        await self._repository.update_status(conv_id, S.CONNECTING)

        try:
            config = {
                'system_instruction': system_instruction,
                'response_modalities': ['AUDIO'],
            }
            await self._gemini_client.aio.live.connect(config=config)
        except Exception:
            logger.error('Gemini session 建立失敗: %s', conv_id)
            self.transition_state(conv_id, S.FAILED)
            await self._repository.update_status(conv_id, S.FAILED)
            return self._build_response(conv_id)

        self.transition_state(conv_id, S.ACTIVE)
        await self._repository.update_status(conv_id, S.ACTIVE)

        return self._build_response(conv_id)

    async def end_conversation(self, conversation_id: str) -> dict[str, Any]:
        conv = self._get_conversation_or_raise(conversation_id)

        if conv['status'] != S.ACTIVE:
            msg = f'Cannot end conversation in {conv["status"]} state'
            raise ValueError(msg)

        try:
            await self._finalize_conversation(conversation_id, conv['transcript'], S.ASSESSING)
        except Exception:
            logger.error('Transcript 儲存失敗，對話標記為 failed: %s', conversation_id)
            self.transition_state(conversation_id, S.FAILED)
            await self._repository.update_status(conversation_id, S.FAILED)

        return self._build_response(conversation_id)

    async def cancel_conversation(self, conversation_id: str) -> dict[str, Any]:
        conv = self._get_conversation_or_raise(conversation_id)

        status = conv['status']
        if status in (S.COMPLETED, S.FAILED, S.CANCELLED, S.ASSESSING):
            msg = f'Cannot cancel conversation in {status} state'
            raise ValueError(msg)

        if status == S.ACTIVE and len(conv['transcript']) > 0:
            await self._finalize_conversation(conversation_id, conv['transcript'], S.ASSESSING)
        else:
            self.transition_state(conversation_id, S.CANCELLED)
            await self._repository.update_status(conversation_id, S.CANCELLED)

        self._cleanup_conversation(conversation_id)

        return self._build_response(conversation_id)

    def get_state(self, conversation_id: str) -> dict[str, Any] | None:
        return self._conversations.get(conversation_id)

    async def get_history(self, user_id: str) -> list[dict[str, Any]]:
        return await self._repository.list_by_user(user_id)

    async def has_active_conversation(self, user_id: str) -> bool:
        for conv in self._conversations.values():
            if conv['user_id'] == user_id and conv['status'] in (
                S.PREPARING,
                S.CONNECTING,
                S.ACTIVE,
            ):
                return True
        return False

    def transition_state(self, conversation_id: str, new_status: str) -> None:
        conv = self._get_conversation_or_raise(conversation_id)

        current = conv['status']
        valid = VALID_TRANSITIONS.get(ConversationStatus(current), set())
        if new_status not in valid:
            msg = f'Invalid transition from {current} to {new_status}'
            raise ValueError(msg)

        conv['status'] = new_status

    async def handle_disconnection(self, conversation_id: str) -> None:
        conv = self._conversations.get(conversation_id)
        if not conv:
            return

        try:
            await self._save_transcript_with_retry(conversation_id, conv['transcript'])
        except Exception:
            logger.exception('Transcript 儲存失敗 (disconnection): %s', conversation_id)

        self.transition_state(conversation_id, S.FAILED)
        await self._repository.update_status(conversation_id, S.FAILED)

    async def handle_silence_timeout(self, conversation_id: str) -> None:
        conv = self._conversations.get(conversation_id)
        if not conv:
            return

        await self._finalize_conversation(conversation_id, conv['transcript'], S.ASSESSING)

        self._notifications_sent[conversation_id] = {
            'type': 'silence_timeout',
            'message': '對話因靜默超時已自動結束',
        }

    async def on_audio_received(self, conversation_id: str) -> None:
        self._silence_timers[conversation_id] = asyncio.get_event_loop().time()

    # --- Private ---

    def _get_conversation_or_raise(self, conversation_id: str) -> dict[str, Any]:
        conv = self._conversations.get(conversation_id)
        if not conv:
            msg = f'Conversation {conversation_id} not found'
            raise ValueError(msg)
        return conv

    def _build_response(self, conversation_id: str) -> dict[str, Any]:
        conv = self._conversations[conversation_id]
        return {
            'conversation_id': conversation_id,
            'status': conv['status'],
        }

    async def _finalize_conversation(
        self,
        conversation_id: str,
        transcript: list[dict[str, Any]],
        target_status: ConversationStatus,
    ) -> None:
        await self._save_transcript_with_retry(conversation_id, transcript)
        await self._repository.update_ended_at(conversation_id, datetime.now(UTC))
        self.transition_state(conversation_id, target_status)
        await self._repository.update_status(conversation_id, target_status)

    async def _call_scenario_designer_with_retry(self, source_type: str, source_ref: str) -> str:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return await self._scenario_designer(source_type, source_ref)
            except (TimeoutError, ConnectionError, OSError) as e:
                last_error = e
                if attempt == 0:
                    logger.warning('scenario_designer 第 %d 次呼叫失敗，重試中', attempt + 1)
                    continue
        raise last_error  # type: ignore[misc]

    async def _save_transcript_with_retry(
        self, conversation_id: str, transcript: list[dict[str, Any]]
    ) -> None:
        last_error: Exception | None = None
        for attempt in range(_TRANSCRIPT_RETRY_COUNT):
            try:
                await self._repository.save_transcript(conversation_id, transcript)
                return
            except Exception as e:
                last_error = e
                logger.error(
                    'Transcript 儲存失敗 (attempt %d/%d): %s',
                    attempt + 1,
                    _TRANSCRIPT_RETRY_COUNT,
                    e,
                )
                if attempt < len(_TRANSCRIPT_RETRY_DELAYS):
                    await asyncio.sleep(_TRANSCRIPT_RETRY_DELAYS[attempt])
        raise last_error  # type: ignore[misc]

    async def _on_time_limit_warning(self, conversation_id: str) -> None:
        self._warning_sent[conversation_id] = True
        self._notifications_sent[conversation_id] = {
            'type': 'time_warning',
            'message': '對話將在 2 分鐘後自動結束',
        }

    async def _on_time_limit_reached(self, conversation_id: str) -> None:
        conv = self._conversations.get(conversation_id)
        if not conv or conv['status'] != S.ACTIVE:
            return

        await self._finalize_conversation(conversation_id, conv['transcript'], S.ASSESSING)

    def _cleanup_conversation(self, conversation_id: str) -> None:
        self._warning_sent.pop(conversation_id, None)
        self._silence_timers.pop(conversation_id, None)
        task = self._timeout_tasks.pop(conversation_id, None)
        if task and not task.done():
            task.cancel()
