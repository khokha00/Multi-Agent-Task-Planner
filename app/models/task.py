from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import TaskStatus


class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:12]}")
    user_request: str
    status: TaskStatus = TaskStatus.QUEUED
    plan_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)