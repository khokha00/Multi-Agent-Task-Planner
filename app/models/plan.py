from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.subtask import Subtask


class ExecutionPlan(BaseModel):
    id: str = Field(default_factory=lambda: f"plan_{uuid4().hex[:8]}")
    task_id: str
    subtasks: list[Subtask]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))