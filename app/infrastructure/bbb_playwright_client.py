from playwright.async_api import Browser, Page, Playwright

from app.core.config import BotSettings
from app.core.exceptions import LectureClientError, LectureJoinError
from app.domain.interfaces import LectureClient
from app.domain.models import ChatMessage, LectureConfig
from app.infrastructure import selectors


class BBBPlaywrightClient(LectureClient):
    def __init__(self, playwright: Playwright, settings: BotSettings):
        self._playwright = playwright
        self._settings = settings
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def start(self) -> None:
        self.browser = await self._playwright.chromium.launch(
            headless=self._settings.headless,
            slow_mo=self._settings.browser_slow_mo_ms,
        )
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(self._settings.page_timeout_ms)

    async def join(self, config: LectureConfig) -> None:
        page = self._require_page()
        try:
            await page.goto(str(config.lecture_url))
            await page.locator(selectors.JOIN_NAME_INPUT).fill(config.student_name)
            await page.locator(selectors.JOIN_BUTTON).click()
            listen_button = page.locator(selectors.LISTEN_ONLY_BUTTON)
            await listen_button.wait_for(
                state="visible", timeout=config.wait_time_till_lecture_start_in_seconds
            )
            await listen_button.click()
        except Exception as error:
            raise LectureJoinError("failed to join lecture") from error

    async def send_message(self, text: str) -> None:
        page = self._require_page()
        try:
            chat_input = page.locator(selectors.CHAT_INPUT)
            await chat_input.wait_for(state="visible")
            await chat_input.fill(text)
            await page.locator(selectors.SEND_MESSAGE_BUTTON).click()
        except Exception as error:
            raise LectureClientError("failed to send chat message") from error

    async def get_messages(self) -> list[ChatMessage]:
        page = self._require_page()
        try:
            texts = await page.locator(selectors.CHAT_MESSAGE_TEXT).all_text_contents()
        except Exception as error:
            raise LectureClientError("failed to read chat messages") from error
        return [ChatMessage(text=text.strip()) for text in texts if text.strip()]

    async def leave(self) -> None:
        page = self._require_page()
        try:
            await page.locator(selectors.OPTIONS_BUTTON).click()
            await page.locator(selectors.LOGOUT_BUTTON).click()
        except Exception as error:
            raise LectureClientError("failed to leave lecture") from error

    async def close(self) -> None:
        try:
            if self.browser is not None:
                await self.browser.close()
        finally:
            await self._playwright.stop()

    def _require_page(self) -> Page:
        if self.page is None:
            raise LectureClientError("browser page is not initialized")
        return self.page
