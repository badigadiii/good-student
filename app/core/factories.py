from playwright.async_api import async_playwright

from app.core.config import BotSettings
from app.domain.interfaces import LectureClientFactory
from app.infrastructure.bbb_playwright_client import BBBPlaywrightClient


class PlaywrightLectureClientFactory(LectureClientFactory):
    def __init__(self, settings: BotSettings):
        self._settings = settings

    async def create(self) -> BBBPlaywrightClient:
        playwright = await async_playwright().start()
        client = BBBPlaywrightClient(playwright=playwright, settings=self._settings)
        await client.start()
        return client
