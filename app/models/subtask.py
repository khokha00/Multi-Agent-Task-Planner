from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import AgentType, SubtaskStatus
from app.models.result import AgentResult  # noqa: E402



class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: f"subtask_{uuid4().hex[:8]}")
    task_id: str
    description: str
    agent_type: AgentType
    dependencies: list[str] = Field(default_factory=list)
    priority: int = 0
    status: SubtaskStatus = SubtaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    result: "AgentResult | None" = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
