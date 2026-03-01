import asyncio
from string import punctuation as PUNCTUATION

from playwright.async_api import async_playwright, Playwright, Page, Browser


class GoodStudent:
    def __init__(self, playwright: Playwright):
        self.lecture_url = "https://bbb.ssau.ru/b/202-2w5-kwd-ilr"
        self.student_name = "Good Student"
        self.greetings_message = "здарова"
        self.goodbye_message = "чао"

        self.keyphrase_lecture_over = ["до свидания", "досвидания"]

        self.playwright = playwright
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def start(self):
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()

    async def join_lecture(self):
        await self.page.goto(self.lecture_url)

        name_field_selector = "input.join-form"
        await self.page.locator(name_field_selector).fill(self.student_name)

        join_button_selector = "#room-join"
        await self.page.locator(join_button_selector).click()

        listen_button_selector = "button[data-test='listenOnlyBtn']"
        await self.page.locator(listen_button_selector).wait_for(state="visible")
        await self.page.locator(listen_button_selector).click()

    async def send_message(self, text: str):
        chat_selector = "#message-input"
        send_button_selector = "button[data-test='sendMessageButton']"

        await self.page.locator(chat_selector).wait_for(state="visible")
        await self.page.locator(chat_selector).fill(text)
        await self.page.locator(send_button_selector).click()

    async def left_lecture(self):
        options_button_selector = "[data-test='optionsButton']"
        logout_button_selector = "[data-key='menuItem-logout']"

        await self.page.locator(options_button_selector).click()
        await self.page.locator(logout_button_selector).click()

    async def get_messages_from_chat(self):
        messages_locator = self.page.locator('p[data-test="chatUserMessageText"]')

        await messages_locator.first.wait_for(state="visible")
        texts = await messages_locator.all_text_contents()
        return [text.strip() for text in texts]

    def clean_string(self, string: str) -> str:
        for char in PUNCTUATION:
            string = string.replace(char, " ")
        return string.lower().strip()

    def is_lecture_over(self, texts: list[str]) -> bool:
        recent_texts = texts[-10:]
        recent_texts = [self.clean_string(text) for text in recent_texts]

        matches = 0

        for text in recent_texts:
            if any(phrase in text for phrase in self.keyphrase_lecture_over):
                matches += 1

        return matches >= 3

    async def run(self):
        await self.join_lecture()

        await self.page.wait_for_timeout(1000)
        await self.send_message(self.greetings_message)

        while True:
            messages = await self.get_messages_from_chat()
            if self.is_lecture_over(messages[-10:]):
                break

            await self.page.wait_for_timeout(3000)

        await self.page.wait_for_timeout(1000)
        await self.send_message(self.goodbye_message)

        await self.page.wait_for_timeout(1000)
        await self.left_lecture()


async def main():
    async with async_playwright() as playwright:
        student = GoodStudent(playwright)

        # messages = ["до свидания", "до свидания!!!", "спасибо за лекцию, до свидания"]
        # do_quit = student.is_lecture_over(messages)
        # if do_quit:
        #     print("Выхожу")
        # else:
        #     print("Сижу дальше")

        await student.start()
        await student.run()
        await student.close()


if __name__ == "__main__":
    asyncio.run(main())