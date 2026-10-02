from typing import TypedDict

from app.models.plan import ExecutionPlan
from app.models.result import AgentResult
from app.models.subtask import Subtask
from app.models.task import Task


class GraphState(TypedDict, total=False):
    task: Task
    plan: ExecutionPlan
    subtasks: list[Subtask]                 # mutable working copy, statuses updated in place
    results: dict[str, AgentResult]          # subtask_id -> result
    waves_completed: int
    error: str | None