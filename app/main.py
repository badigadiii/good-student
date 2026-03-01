from datetime import datetime

from pydantic import AnyUrl

from app.core.config import BotSettings
from app.core.factories import PlaywrightLectureClientFactory
from app.domain.lecture_bot import LectureBot
from app.domain.models import LectureConfig


def build_demo_lecture_config() -> LectureConfig:
    return LectureConfig(
        lecture_url=AnyUrl("https://bbb.ssau.ru/b/202-2w5-kwd-ilr"),
        student_name="Good Student",
        greetings_message="здарова",
        goodbye_message="чао",
        lecture_start=None,
        lecture_end=None,
        keyphrase_lecture_over=["до свидания", "досвидания", "всего хорошего"],
    )


async def main() -> None:
    settings = BotSettings()
    config = build_demo_lecture_config()
    factory = PlaywrightLectureClientFactory(settings=settings)
    client = await factory.create()
    bot = LectureBot(config=config, client=client, settings=settings)
    await bot.run(now_provider=datetime.now)
