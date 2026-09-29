from pydantic import BaseModel, Field

from app.models.result import AgentResult


class AgentContext(BaseModel):
    task_id: str
    subtask_id: str
    user_goal: str
    # results of the subtasks this one depends on, keyed by subtask id
    dependency_results: dict[str, AgentResult] = Field(default_factory=dict)