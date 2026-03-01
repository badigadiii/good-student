import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.core.config import BotSettings
from app.core.factories import PlaywrightLectureClientFactory
from app.domain.lecture_bot import LectureBot
from app.domain.models import LectureConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ManagedBot:
    bot_id: str
    config: LectureConfig
    task: asyncio.Task[None]
    created_at: datetime

    @property
    def status(self) -> str:
        if self.task.cancelled():
            return "cancelled"
        if self.task.done():
            return "failed" if self.task.exception() is not None else "finished"
        return "running"


class BotManager:
    def __init__(
        self,
        settings: BotSettings,
        now_provider: Callable[..., datetime] = datetime.now,
    ) -> None:
        self._settings = settings
        self._now_provider = now_provider
        self._bots: dict[str, ManagedBot] = {}

    async def start_bot(self, config: LectureConfig) -> ManagedBot:
        bot_id = str(uuid4())
        factory = PlaywrightLectureClientFactory(settings=self._settings)
        client = await factory.create()
        bot = LectureBot(config=config, client=client, settings=self._settings)
        task = asyncio.create_task(
            self._run_bot(bot_id=bot_id, bot=bot), name=f"lecture-bot-{bot_id}"
        )
        managed_bot = ManagedBot(
            bot_id=bot_id,
            config=config,
            task=task,
            created_at=self._now_provider(config.lecture_end.tzinfo)
            if config.lecture_end
            else self._now_provider(),
        )
        self._bots[bot_id] = managed_bot
        logger.info("Started bot id=%s student=%s", bot_id, config.student_name)
        return managed_bot

    def list_bots(self) -> list[ManagedBot]:
        return sorted(self._bots.values(), key=lambda bot: bot.created_at)

    def get_bot(self, bot_id: str) -> ManagedBot | None:
        return self._bots.get(bot_id)

    async def stop_bot(self, bot_id: str) -> bool:
        managed_bot = self._bots.get(bot_id)
        if managed_bot is None:
            return False
        await self._cancel_bot(managed_bot)
        return True

    async def shutdown(self) -> None:
        for managed_bot in list(self._bots.values()):
            await self._cancel_bot(managed_bot)

    async def _run_bot(self, bot_id: str, bot: LectureBot) -> None:
        try:
            await bot.run(now_provider=self._now_provider)
        except asyncio.CancelledError:
            logger.info("Bot id=%s cancelled", bot_id)
            raise
        except Exception:
            logger.exception("Bot id=%s failed", bot_id)
            raise
        finally:
            logger.info("Bot id=%s finished", bot_id)

    async def _cancel_bot(self, managed_bot: ManagedBot) -> None:
        task = managed_bot.task
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._bots.pop(managed_bot.bot_id, None)
        logger.info("Stopped bot id=%s", managed_bot.bot_id)
