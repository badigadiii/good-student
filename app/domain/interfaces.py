from abc import ABC, abstractmethod

from app.domain.models import ChatMessage, LectureConfig


class LectureClient(ABC):
    @abstractmethod
    async def join(self, config: LectureConfig) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(self) -> list[ChatMessage]:
        raise NotImplementedError

    @abstractmethod
    async def leave(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class LectureClientFactory(ABC):
    @abstractmethod
    async def create(self) -> LectureClient:
        raise NotImplementedError
