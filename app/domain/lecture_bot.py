import logging
import string
from collections.abc import Callable, Sequence
from datetime import datetime

from app.core.config import BotSettings
from app.domain.interfaces import LectureClient
from app.domain.models import ChatMessage, LectureConfig

logger = logging.getLogger(__name__)


class LectureBot:
    def __init__(self, config: LectureConfig, client: LectureClient, settings: BotSettings):
        self._config = config
        self._client = client
        self._settings = settings

    def normalize_text(self, text: str) -> str:
        normalized = text.lower()
        for char in string.punctuation:
            normalized = normalized.replace(char, " ")
        return " ".join(normalized.split())

    def is_lecture_over_by_keyphrases(self, messages: Sequence[ChatMessage]) -> bool:
        recent_messages = messages[-self._settings.RECENT_MESSAGES_LIMIT :]
        matches = 0
        for message in recent_messages:
            normalized = self.normalize_text(message.text)
            if any(phrase in normalized for phrase in self._config.keyphrase_lecture_over):
                matches += 1
        return matches >= self._settings.KEYPHRASE_MATCH_THRESHOLD

    def is_lecture_over_by_time(self, now: datetime) -> bool:
        lecture_end = self._config.lecture_end
        return lecture_end is not None and now >= lecture_end

    def should_finish(self, messages: Sequence[ChatMessage], now: datetime) -> bool:
        return self.is_lecture_over_by_keyphrases(messages) or self.is_lecture_over_by_time(now)

    async def run(self, now_provider: Callable[..., datetime]) -> None:
        try:
            logger.info("Lecture bot run started for student=%s", self._config.student_name)
            if self._config.lecture_start:
                logger.debug(
                    "Waiting for lecture start at %s",
                    self._config.lecture_start.isoformat(),
                )
                while True:
                    current_time = self._current_time(now_provider)
                    if current_time >= self._config.lecture_start:
                        logger.info("Lecture start time reached at %s", current_time.isoformat())
                        break
                    logger.debug(
                        "Lecture has not started yet, current_time=%s",
                        current_time.isoformat(),
                    )
                    await self._sleep(self._settings.lecture_start_poll_interval_ms)

            logger.info("Joining lecture at %s", self._config.lecture_url)
            await self._client.join(self._config)
            await self._sleep(self._settings.post_join_delay_ms)
            logger.info("Sending greeting message")
            await self._client.send_message(self._config.greetings_message)

            while True:
                messages = await self._client.get_messages()
                current_time = self._current_time(now_provider)
                if self.is_lecture_over_by_keyphrases(messages):
                    logger.info("Lecture finish detected by keyphrases: %s", messages)
                    break
                if self.is_lecture_over_by_time(current_time):
                    logger.info(
                        "Lecture finish detected by schedule at %s", current_time.isoformat()
                    )
                    break
                await self._sleep(self._settings.chat_poll_interval_ms)

            await self._sleep(self._settings.pre_goodbye_delay_ms)
            logger.info("Sending goodbye message")
            await self._client.send_message(self._config.goodbye_message)
            await self._sleep(self._settings.pre_leave_delay_ms)
            logger.info("Leaving lecture")
            await self._client.leave()
        finally:
            logger.debug("Closing lecture client")
            await self._client.close()

    def _current_time(self, now_provider: Callable[..., datetime]) -> datetime:
        if self._config.lecture_end is not None:
            return now_provider(self._config.lecture_end.tzinfo)
        return now_provider()

    async def _sleep(self, delay_ms: int) -> None:
        if delay_ms > 0:
            import asyncio

            await asyncio.sleep(delay_ms / 1000)
