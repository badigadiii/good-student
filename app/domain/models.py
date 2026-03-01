from datetime import datetime

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ChatMessage(BaseModel):
    text: str


class LectureConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    lecture_url: AnyUrl
    student_name: str = Field(min_length=1, max_length=100)
    greetings_message: str = Field(min_length=1, max_length=1000)
    goodbye_message: str = Field(min_length=1, max_length=1000)
    lecture_start: datetime | None = None
    lecture_end: datetime | None = None
    keyphrase_lecture_over: list[str] = Field(min_length=1)
    wait_time_till_lecture_start_in_seconds: int | None = Field(default=90 * 60 * 1000)

    @field_validator("lecture_start", "lecture_end")
    @classmethod
    def validate_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return value

    @field_validator("keyphrase_lecture_over")
    @classmethod
    def normalize_keyphrases(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for phrase in value:
            cleaned = phrase.strip().lower()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        if not normalized:
            raise ValueError(
                "keyphrase_lecture_over must contain at least one non-empty phrase"
            )
        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "LectureConfig":
        if (
            self.lecture_start is not None
            and self.lecture_end is not None
            and self.lecture_end <= self.lecture_start
        ):
            raise ValueError("lecture_end must be greater than lecture_start")
        return self
