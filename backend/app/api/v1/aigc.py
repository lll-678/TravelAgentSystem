from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.aigc_agent_service import run_aigc_agent
from app.services.aigc_service import generate_diary_draft, generate_storyboard

router = APIRouter()


class DiaryDraftRequest(BaseModel):
    topic: str = Field(default="沙河校区游览", max_length=120)
    keywords: list[str] = Field(default_factory=list)
    tone: str = Field(default="自然", max_length=40)


class StoryboardRequest(BaseModel):
    text: str = Field(min_length=1)
    scene_count: int = Field(default=4, ge=1, le=8)
    media_urls: list[str] = Field(default_factory=list)


class AigcAgentRequest(BaseModel):
    task: str = Field(default="diary_animation", pattern="^(diary_animation|diary_draft|storyboard)$")
    text: str = Field(min_length=1, max_length=4000)
    destination_name: str = Field(default="北京邮电大学沙河校区", max_length=120)
    style: str = Field(default="natural", max_length=40)
    media_urls: list[str] = Field(default_factory=list)
    scene_count: int = Field(default=4, ge=1, le=8)
    user_id: int | None = Field(default=None, ge=1)
    diary_id: int | None = Field(default=None, ge=1)


@router.post("/diary-draft")
def diary_draft(payload: DiaryDraftRequest) -> dict:
    return generate_diary_draft(payload.model_dump())


@router.post("/storyboard")
def storyboard(payload: StoryboardRequest) -> dict:
    return generate_storyboard(payload.model_dump())


@router.post("/agent/run")
def aigc_agent(payload: AigcAgentRequest) -> dict:
    return run_aigc_agent(payload.model_dump())
