from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.schemas import BotDetail, BotSummary, StartBotRequest
from app.application.bot_manager import BotManager, ManagedBot

router = APIRouter(prefix="/bots", tags=["bots"])


def get_bot_manager() -> BotManager:
    raise RuntimeError("BotManager dependency is not configured")


BotManagerDependency = Annotated[BotManager, Depends(get_bot_manager)]


def to_summary(bot: ManagedBot) -> BotSummary:
    return BotSummary(
        id=bot.bot_id,
        student_name=bot.config.student_name,
        lecture_url=str(bot.config.lecture_url),
        status=bot.status,
        created_at=bot.created_at,
    )


def to_detail(bot: ManagedBot) -> BotDetail:
    return BotDetail(
        **to_summary(bot).model_dump(),
        greetings_message=bot.config.greetings_message,
        goodbye_message=bot.config.goodbye_message,
        keyphrase_lecture_over=bot.config.keyphrase_lecture_over,
    )


@router.post("", response_model=BotDetail, status_code=status.HTTP_201_CREATED)
async def start_bot(
    request: StartBotRequest,
    bot_manager: BotManagerDependency,
) -> BotDetail:
    bot = await bot_manager.start_bot(request.to_lecture_config())
    return to_detail(bot)


@router.get("", response_model=list[BotSummary])
async def list_bots(bot_manager: BotManagerDependency) -> list[BotSummary]:
    return [to_summary(bot) for bot in bot_manager.list_bots()]


@router.get("/{bot_id}", response_model=BotDetail)
async def get_bot(bot_id: str, bot_manager: BotManagerDependency) -> BotDetail:
    bot = bot_manager.get_bot(bot_id)
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    return to_detail(bot)


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: str,
    bot_manager: BotManagerDependency,
) -> Response:
    was_stopped = await bot_manager.stop_bot(bot_id)
    if not was_stopped:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
