from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import LectureConfig


class StartBotRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    lecture_url: str
    student_name: str = Field(min_length=1, max_length=100)
    greetings_message: str = Field(min_length=1, max_length=1000)
    goodbye_message: str = Field(min_length=1, max_length=1000)
    keyphrase_lecture_over: list[str] | None = None

    def to_lecture_config(self) -> LectureConfig:
        return LectureConfig(**self.model_dump(exclude_none=True))


class BotSummary(BaseModel):
    id: str
    student_name: str
    lecture_url: str
    status: str
    created_at: datetime


class BotDetail(BotSummary):
    greetings_message: str
    goodbye_message: str
    keyphrase_lecture_over: list[str]
