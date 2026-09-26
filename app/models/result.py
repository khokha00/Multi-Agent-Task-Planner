from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    subtask_id: str
    agent_type: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    tokens_used: int | None = None
    duration_seconds: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))